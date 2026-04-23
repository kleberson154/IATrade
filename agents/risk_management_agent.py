"""
Agente de Gerenciamento de Risco
Calcula sizing, stops, TPs, valida RR
Essencial: Position Sizing e Risk Management são a ESTRATÉGIA
"""

import logging
from typing import Optional, Dict, Tuple
from models.trade_models import Trade, SetupSignal, PositionSize, TradeDirection
from core.position_sizing import PositionSizer
from core.volatility import VolatilityCalculator
from config.settings import MIN_RR_RATIO, RISK_PER_TRADE_PERCENT, ACCOUNT_SIZE_USDT


class RiskManagementAgent:
    """
    Agente responsável por:
    - Calcular tamanho da posição
    - Definir stops e take profits
    - Validar RR ratio
    - Gerenciar risco por trade
    - Manter disciplina de sizing
    """
    
    def __init__(self, agent_id: str = "RM-001"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        
        self.position_sizer = PositionSizer(
            account_size=ACCOUNT_SIZE_USDT,
            risk_percent=RISK_PER_TRADE_PERCENT
        )
        self.volatility_calc = VolatilityCalculator()
        
        # Histórico para monitorar disciplina
        self.sizing_history = []
        self.consecutive_losses = 0
    
    def calculate_trade_setup(self, signal: SetupSignal, candle_data: Dict,
                             volatility_data = None) -> Optional[Trade]:
        """
        Cria setup de trade completo baseado no sinal
        
        Retorna Trade com entry, stops, TPs todos calculados
        """
        trade = Trade(
            symbol="BTCUSDT",
            direction=signal.direction,
            setup_type=signal.setup_type,
            entry_price=signal.entry_price,
            entry_size=0.0,  # Será calculado
        )
        
        # 1. Calcula stop loss
        stop_loss = signal.stop_price
        
        # Validação básica: stop deve estar do lado correto
        if signal.direction == TradeDirection.LONG:
            if stop_loss >= signal.entry_price:
                self.logger.error(f"Stop inválido para LONG: {stop_loss} >= {signal.entry_price}")
                return None
        else:  # SHORT
            if stop_loss <= signal.entry_price:
                self.logger.error(f"Stop inválido para SHORT: {stop_loss} <= {signal.entry_price}")
                return None
        
        trade.stop_loss = stop_loss
        
        # 2. Calcula risk amount
        trade.risk_amount = self.position_sizer.calculate_risk_amount()
        
        # 3. Calcula position size
        try:
            position_size = self.position_sizer.calculate_position_size(
                signal.entry_price,
                stop_loss
            )
        except ValueError as e:
            self.logger.error(f"Erro ao calcular position size: {e}")
            return None
        
        trade.entry_size = position_size
        
        # 4. Ajusta por volatilidade se disponível
        if volatility_data:
            volatility_pct = volatility_data.get("atr_percent", 0.5)
            adjustment = self.volatility_calc.calculate_position_size_adjustment(
                volatility_pct, position_size
            )
            trade.entry_size = adjustment
            self.logger.info(f"Position size ajustado por volatilidade: {position_size:.4f} -> {adjustment:.4f}")
        
        # 5. Calcula take profits (Multi-TP)
        # Usa RR mínimo para TP1, maior para TP3
        rr_tp1 = MIN_RR_RATIO * 0.8  # TP1 um pouco mais perto
        rr_tp2 = MIN_RR_RATIO * 1.0
        rr_tp3 = MIN_RR_RATIO * 1.3  # TP3 mais longe
        
        tp_calc = self.position_sizer.calculate_take_profits(
            signal.entry_price,
            stop_loss,
            rr_ratio=rr_tp2
        )
        
        trade.tp1 = tp_calc["tp1"]
        trade.tp2 = tp_calc["tp2"]
        trade.tp3 = tp_calc["tp3"]
        
        # Ajusta baseado em RR
        if signal.direction == TradeDirection.LONG:
            trade.tp1 = signal.entry_price + (signal.entry_price - stop_loss) * 0.6
            trade.tp2 = signal.entry_price + (signal.entry_price - stop_loss) * 1.0
            trade.tp3 = signal.entry_price + (signal.entry_price - stop_loss) * 1.5
        else:  # SHORT
            trade.tp1 = signal.entry_price - (stop_loss - signal.entry_price) * 0.6
            trade.tp2 = signal.entry_price - (stop_loss - signal.entry_price) * 1.0
            trade.tp3 = signal.entry_price - (stop_loss - signal.entry_price) * 1.5
        
        # 6. Calcula reward amount e RR ratio
        stop_distance = abs(signal.entry_price - stop_loss)
        trade.rr_ratio = tp_calc["rr_ratio"]
        trade.reward_amount = trade.entry_size * (abs(trade.tp2 - signal.entry_price))
        
        self.logger.info(f"Trade setup criado: {trade}")
        
        return trade
    
    def validate_trade_risk(self, trade: Trade) -> Tuple[bool, str]:
        """
        Valida se a trade segue regras de risco
        
        Returns:
            (é_válido: bool, mensagem: str)
        """
        # Regra 1: RR mínimo
        if trade.rr_ratio < MIN_RR_RATIO:
            return False, f"RR baixo: {trade.rr_ratio:.2f}x (min: {MIN_RR_RATIO}x)"
        
        # Regra 2: Risk por trade não pode exceder limite
        max_risk = ACCOUNT_SIZE_USDT * (RISK_PER_TRADE_PERCENT / 100)
        if trade.risk_amount > max_risk:
            return False, f"Risk muito alto: ${trade.risk_amount:.2f} (max: ${max_risk:.2f})"
        
        # Regra 3: Position size deve ser > 0
        if trade.entry_size <= 0:
            return False, "Position size inválido"
        
        # Regra 4: Entry, SL, TPs devem estar coerentes
        if trade.direction == TradeDirection.LONG:
            if not (trade.stop_loss < trade.entry_price < trade.tp1 < trade.tp2 < trade.tp3):
                return False, "Preços não estão em ordem lógica para LONG"
        else:  # SHORT
            if not (trade.tp3 < trade.tp2 < trade.tp1 < trade.entry_price < trade.stop_loss):
                return False, "Preços não estão em ordem lógica para SHORT"
        
        # Regra 5: Nunca aumentar size após loss (verifica histórico)
        if self.consecutive_losses > 0 and trade.entry_size > self._get_average_recent_size():
            return False, f"Tentativa de aumentar size após {self.consecutive_losses} loss(es)"
        
        return True, "Trade válida"
    
    def _get_average_recent_size(self) -> float:
        """Retorna size médio das últimas 5 trades"""
        if not self.sizing_history:
            return 0.0
        
        recent = self.sizing_history[-5:]
        return sum(recent) / len(recent)
    
    def record_trade_execution(self, trade: Trade):
        """Registra execução da trade para histório de sizing"""
        self.sizing_history.append(trade.entry_size)
        if len(self.sizing_history) > 100:
            self.sizing_history = self.sizing_history[-100:]
    
    def record_trade_result(self, trade: Trade):
        """Registra resultado da trade"""
        if not trade.is_profitable:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def should_pause_trading(self) -> Tuple[bool, str]:
        """
        Verifica se deve pausar trading (regra de disciplina)
        """
        from config.settings import STOP_AFTER_2_LOSSES
        
        if STOP_AFTER_2_LOSSES and self.consecutive_losses >= 2:
            return True, f"Pausa de trading após {self.consecutive_losses} perdas"
        
        return False, ""
    
    def get_position_summary(self, trade: Trade) -> str:
        """Retorna resumo da posição formatado"""
        return (
            f"BTC: {trade.entry_size:.4f} | "
            f"Entry: ${trade.entry_price:.2f} | "
            f"SL: ${trade.stop_loss:.2f} ({abs(trade.entry_price - trade.stop_loss):.2f}) | "
            f"TP1/2/3: ${trade.tp1:.2f}/${trade.tp2:.2f}/${trade.tp3:.2f} | "
            f"Risk: ${trade.risk_amount:.2f} | "
            f"RR: {trade.rr_ratio:.2f}x"
        )
    
    def get_agent_status(self) -> str:
        """Retorna status do agente"""
        return (
            f"Agent: {self.agent_id} | "
            f"Consecutive losses: {self.consecutive_losses} | "
            f"Avg recent size: {self._get_average_recent_size():.4f} BTC"
        )
