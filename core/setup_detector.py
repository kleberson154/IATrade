"""
Setup Detector - Identifica Momentum, Mean Reversion e Breakouts
Essencial para o artigo: Remove randomness das decisões
"""

import numpy as np
from typing import Optional, List
from models.trade_models import SetupSignal, TradeDirection


class SetupDetector:
    """Detecta os 3 tipos principais de setups do artigo"""
    
    def __init__(self):
        self.min_bars_for_analysis = 20  # Mínimo de candles para análise
    
    def detect_momentum(self, closes: List[float], highs: List[float], 
                       lows: List[float], current_price: float) -> Optional[SetupSignal]:
        """
        MOMENTUM: Preço quebra estrutura e continua
        
        Sinais:
        - Breakout de resistência recente
        - Candles consecutivos na mesma direção
        - Volume crescente (não temos aqui, mas mencionamos)
        - Preço acima de MA (trend)
        """
        if len(closes) < self.min_bars_for_analysis:
            return None
        
        recent_closes = closes[-10:]
        ma_20 = sum(closes[-20:]) / 20
        
        # LONG: Quebra resistência, MA crescendo
        resistance = max(highs[-15:-5])
        support = min(lows[-15:-5])
        
        # Verifica se está em tendência alta
        if current_price > ma_20:
            # Verificar se tem momentum
            consecutive_up = 0
            for i in range(len(recent_closes)-1, 0, -1):
                if recent_closes[i] > recent_closes[i-1]:
                    consecutive_up += 1
                else:
                    break
            
            if consecutive_up >= 3 and current_price > resistance:
                # Encontrou momentum LONG
                entry = current_price
                stop = support - (support * 0.01)  # 1% abaixo do suporte
                
                return SetupSignal(
                    setup_type="momentum",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.LONG,
                    confidence=0.65 + (min(consecutive_up / 5, 0.35)),  # Max 100%
                    entry_price=entry,
                    stop_price=stop,
                    reason=f"Quebra de resistência com {consecutive_up} candles consecutivos UP"
                )
        
        # SHORT: Quebra suporte, MA caindo
        if current_price < ma_20:
            consecutive_down = 0
            for i in range(len(recent_closes)-1, 0, -1):
                if recent_closes[i] < recent_closes[i-1]:
                    consecutive_down += 1
                else:
                    break
            
            if consecutive_down >= 3 and current_price < support:
                entry = current_price
                stop = resistance + (resistance * 0.01)
                
                return SetupSignal(
                    setup_type="momentum",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.SHORT,
                    confidence=0.65 + (min(consecutive_down / 5, 0.35)),
                    entry_price=entry,
                    stop_price=stop,
                    reason=f"Quebra de suporte com {consecutive_down} candles consecutivos DOWN"
                )
        
        return None
    
    def detect_mean_reversion(self, closes: List[float], highs: List[float],
                             lows: List[float], current_price: float) -> Optional[SetupSignal]:
        """
        MEAN REVERSION: Preço se estende muito e volta
        
        Melhor em RANGE (não em trend)
        Sinais:
        - Preço toca extremo (high/low recente)
        - RSI overbought (>70) ou oversold (<30)
        - Pullback para média móvel
        
        BUG FIX: Stop deve estar SEMPRE baseado na entrada (não em recent_low/high)
        - LONG: Stop = Entry - (range * factor) [ABAIXO da entrada]
        - SHORT: Stop = Entry + (range * factor) [ACIMA da entrada]
        """
        if len(closes) < self.min_bars_for_analysis:
            return None
        
        ma_20 = sum(closes[-20:]) / 20
        ma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma_20
        
        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        range_width = recent_high - recent_low
        
        # RSI simplificado (delta positivos vs negativos)
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = sum(max(d, 0) for d in deltas[-14:]) / 14
        losses = sum(abs(min(d, 0)) for d in deltas[-14:]) / 14
        rs = gains / losses if losses > 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        # Mean Reversion LONG: Tocar fundo em range, RSI oversold
        # Preço está perto do recent_low (fundo do range)
        if current_price <= recent_low + (range_width * 0.2) and rsi < 30:
            if ma_20 > ma_50:  # Tendência está acima (range em contexto bullish)
                # CORRIGIDO: Stop deve estar ABAIXO da entrada
                stop_price = current_price - (range_width * 0.15)
                
                return SetupSignal(
                    setup_type="mean_reversion",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.LONG,
                    confidence=0.55,
                    entry_price=current_price,
                    stop_price=stop_price,
                    reason=f"Mean Reversion LONG: Oversold (RSI={rsi:.0f}), toque no fundo da range"
                )
        
        # Mean Reversion SHORT: Tocar topo em range, RSI overbought
        # Preço está perto do recent_high (topo do range)
        if current_price >= recent_high - (range_width * 0.2) and rsi > 70:
            if ma_20 < ma_50:  # Tendência está abaixo (range em contexto bearish)
                # CORRIGIDO: Stop deve estar ACIMA da entrada
                stop_price = current_price + (range_width * 0.15)
                
                return SetupSignal(
                    setup_type="mean_reversion",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.SHORT,
                    confidence=0.55,
                    entry_price=current_price,
                    stop_price=stop_price,
                    reason=f"Mean Reversion SHORT: Overbought (RSI={rsi:.0f}), toque no topo da range"
                )
        
        return None
    
    def detect_breakout(self, closes: List[float], highs: List[float],
                       lows: List[float], current_price: float, volumes: List[float] = None) -> Optional[SetupSignal]:
        """
        BREAKOUT: Compressão seguida de rompimento
        
        Sinais:
        - ATR diminuiu (compressão)
        - Agora quebra limite com força
        - Payoff assimétrico
        """
        if len(closes) < 30:
            return None
        
        # Calcula ATR dos últimos 20 candles (compressão)
        tr_values_recent = []
        for i in range(len(closes) - 20, len(closes)):
            if i > 0:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values_recent.append(tr)
        
        # ATR dos 30-50 candles atrás (histórico)
        tr_values_old = []
        for i in range(max(0, len(closes) - 50), len(closes) - 20):
            if i > 0:
                tr = max(
                    highs[i] - lows[i],
                    abs(highs[i] - closes[i-1]),
                    abs(lows[i] - closes[i-1])
                )
                tr_values_old.append(tr)
        
        if not tr_values_recent or not tr_values_old:
            return None
        
        atr_recent = sum(tr_values_recent) / len(tr_values_recent)
        atr_old = sum(tr_values_old) / len(tr_values_old)
        
        # Compressão detectada?
        if atr_recent < atr_old * 0.7:
            # Agora procura o breakout
            squeeze_high = max(highs[-20:])
            squeeze_low = min(lows[-20:])
            squeeze_range = squeeze_high - squeeze_low
            
            # Breakout LONG: Quebra squeeze high
            if current_price > squeeze_high:
                return SetupSignal(
                    setup_type="breakout",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.LONG,
                    confidence=0.70,
                    entry_price=current_price,
                    stop_price=squeeze_low,
                    reason=f"Breakout LONG após compressão. Range: {squeeze_range:.2f}"
                )
            
            # Breakout SHORT: Quebra squeeze low
            if current_price < squeeze_low:
                return SetupSignal(
                    setup_type="breakout",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.SHORT,
                    confidence=0.70,
                    entry_price=current_price,
                    stop_price=squeeze_high,
                    reason=f"Breakout SHORT após compressão. Range: {squeeze_range:.2f}"
                )
        
        return None
    
    def detect_all_setups(self, closes: List[float], highs: List[float],
                         lows: List[float], current_price: float) -> List[SetupSignal]:
        """
        Detecta todos os setups e retorna lista ordenada por confiança
        """
        signals = []
        
        # Tenta cada tipo de setup
        momentum = self.detect_momentum(closes, highs, lows, current_price)
        if momentum:
            signals.append(momentum)
        
        mean_rev = self.detect_mean_reversion(closes, highs, lows, current_price)
        if mean_rev:
            signals.append(mean_rev)
        
        breakout = self.detect_breakout(closes, highs, lows, current_price)
        if breakout:
            signals.append(breakout)
        
        # Ordena por confiança (decrescente)
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals


class SetupValidator:
    """Valida setups contra regras de risco e timing"""
    
    @staticmethod
    def validate_setup_signal(signal: SetupSignal, min_confidence: float = 0.50,
                             min_rr: float = 1.5) -> tuple:
        """
        Valida um sinal de setup
        
        Returns:
            (é_válido: bool, pontos: int, mensagem: str)
        """
        pontos = 0
        motivos = []
        
        # Confiança mínima
        if signal.confidence < min_confidence:
            return False, 0, f"Confiança baixa: {signal.confidence:.0%} (min: {min_confidence:.0%})"
        
        pontos += int(signal.confidence * 100)
        
        # RR mínimo (será validado depois quando soubermos o TP)
        # Por enquanto apenas registramos
        
        motivos.append(f"Setup: {signal.setup_type}")
        motivos.append(f"Confiança: {signal.confidence:.0%}")
        motivos.append(f"Razão: {signal.reason}")
        
        return True, pontos, " | ".join(motivos)
