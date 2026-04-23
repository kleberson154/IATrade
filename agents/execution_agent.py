"""
Agente de Execução
Executa trades com disciplina rigorosa, sem emoção
Regra de ouro: NUNCA desviar do sistema
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Tuple
from models.trade_models import Trade, TradeStatus
from config.settings import DRY_RUN, USE_MARKET_ORDERS, ORDER_TIMEOUT_SECONDS


class ExecutionAgent:
    """
    Agente responsável por:
    - Executar ordens EXATAMENTE conforme calculado
    - Sem desvios emocionais
    - Registrar cada execução
    - Gerenciar saídas (SL, TPs, manual)
    """
    
    def __init__(self, bybit_connector=None, agent_id: str = "EXEC-001"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        
        self.bybit = bybit_connector
        self.dry_run = DRY_RUN
        
        self.executed_trades: Dict[str, Trade] = {}
        self.execution_log = []
    
    def execute_trade(self, trade: Trade) -> Tuple[bool, str]:
        """
        Executa uma trade EXATAMENTE como foi aprovada pelo Risk Manager
        
        Fases:
        1. Abre posição (entry)
        2. Define stop loss
        3. Define take profits múltiplos
        
        Returns:
            (sucesso: bool, mensagem: str)
        """
        try:
            self.logger.info(f"Iniciando execução: {trade}")
            
            if not self.dry_run and not self.bybit:
                return False, "Bybit connector não configurado"
            
            # ===== PHASE 1: Entry =====
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Entry: {trade.direction.value.upper()} {trade.entry_size:.4f} BTC @ ${trade.entry_price:.2f}")
                entry_success = True
                entry_order_id = f"SIM-{trade.id}"
            else:
                entry_success, entry_order_id = self._place_entry_order(trade)
            
            if not entry_success:
                return False, f"Falha ao colocar ordem de entrada: {entry_order_id}"
            
            trade.status = TradeStatus.OPEN
            
            self.logger.info(f"[OK] Entry executado. Order ID: {entry_order_id}")
            
            # ===== PHASE 2: Stop Loss =====
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Stop Loss: {trade.stop_loss:.2f}")
                sl_success = True
            else:
                sl_success = self._set_stop_loss(trade, entry_order_id)
            
            if not sl_success:
                self.logger.warning("Falha ao colocar stop loss (continuando com TPs)")
            
            # ===== PHASE 3: Take Profits Múltiplos =====
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Take Profits:")
                self.logger.info(f"  TP1 (50%): {trade.tp1:.2f} - vender 50% da posição")
                self.logger.info(f"  TP2 (30%): {trade.tp2:.2f} - vender 30% da posição")
                self.logger.info(f"  TP3 (20%): {trade.tp3:.2f} - vender 20% da posição")
                tp_success = True
            else:
                tp_success = self._set_take_profits(trade, entry_order_id)
            
            if not tp_success:
                self.logger.warning("Falha ao colocar take profits")
            
            # Registra execução
            self.executed_trades[trade.id] = trade
            self.execution_log.append({
                "timestamp": datetime.utcnow(),
                "trade_id": trade.id,
                "action": "EXECUTE",
                "success": True,
                "entry": trade.entry_price,
                "size": trade.entry_size,
            })
            
            self.logger.info(f"[CONCLUÍDO] Trade executada completamente! ID: {trade.id}")
            return True, f"Trade {trade.id} executada com sucesso"
        
        except Exception as e:
            self.logger.error(f"Erro ao executar trade: {e}", exc_info=True)
            return False, str(e)
    
    def _place_entry_order(self, trade: Trade) -> Tuple[bool, str]:
        """Coloca ordem de entrada"""
        try:
            if USE_MARKET_ORDERS:
                order_type = "MARKET"
            else:
                order_type = "LIMIT"
            
            self.logger.info(f"Colocando {order_type} order: {trade.direction.value.upper()} {trade.entry_size:.4f} BTC")
            
            order_id = self.bybit.place_order(
                symbol="BTCUSDT",
                side=trade.direction.value.upper(),
                order_type=order_type,
                quantity=trade.entry_size,
                price=trade.entry_price,
                timeout_seconds=ORDER_TIMEOUT_SECONDS
            )
            
            return True, order_id
        
        except Exception as e:
            return False, str(e)
    
    def _set_stop_loss(self, trade: Trade, entry_order_id: str) -> bool:
        """Define stop loss para a posição"""
        try:
            self.logger.info(f"Colocando stop loss @ {trade.stop_loss:.2f}")
            
            self.bybit.set_stop_loss(
                symbol="BTCUSDT",
                order_id=entry_order_id,
                stop_price=trade.stop_loss,
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao colocar stop loss: {e}")
            return False
    
    def _set_take_profits(self, trade: Trade, entry_order_id: str) -> bool:
        """Define múltiplos take profits"""
        try:
            # Bybit permite até 3 TP
            self.logger.info("Colocando take profits múltiplos")
            
            self.bybit.set_take_profits(
                symbol="BTCUSDT",
                order_id=entry_order_id,
                tp_levels={
                    "tp1": {"price": trade.tp1, "percent": 50},  # 50% da posição
                    "tp2": {"price": trade.tp2, "percent": 30},  # 30% da posição
                    "tp3": {"price": trade.tp3, "percent": 20},  # 20% da posição
                }
            )
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao colocar take profits: {e}")
            return False
    
    def close_trade_manual(self, trade: Trade, reason: str = "Manual") -> bool:
        """Fecha trade manualmente (não deve ser comum)"""
        try:
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Fechando trade {trade.id}: {reason}")
                return True
            
            self.logger.warning(f"Fechando trade manualmente: {reason}")
            
            self.bybit.close_position(
                symbol="BTCUSDT",
                trade_id=trade.id
            )
            
            trade.status = TradeStatus.CLOSED
            trade.exit_reason = reason
            
            return True
        
        except Exception as e:
            self.logger.error(f"Erro ao fechar trade: {e}")
            return False
    
    def monitor_open_trades(self) -> Dict:
        """Monitora trades abertas e suas performances"""
        open_trades = {
            tid: trade for tid, trade in self.executed_trades.items()
            if trade.status == TradeStatus.OPEN
        }
        
        return {
            "total_open": len(open_trades),
            "trades": open_trades,
        }
    
    def get_agent_status(self) -> str:
        """Retorna status do agente"""
        open_count = len([t for t in self.executed_trades.values() if t.status == TradeStatus.OPEN])
        
        return (
            f"Agent: {self.agent_id} | "
            f"DRY_RUN: {self.dry_run} | "
            f"Total executadas: {len(self.executed_trades)} | "
            f"Abertas: {open_count}"
        )
