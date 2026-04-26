import numpy as np
from typing import Optional, List
from models.trade_models import SetupSignal, TradeDirection
from utils.indicators import Indicators


class SetupDetector:
    def __init__(self):
        self.min_bars_for_analysis = 100  # Mínimo de candles para análise

    def detect_momentum(self, closes: List[float], highs: List[float], 
                        lows: List[float], current_price: float, volumes: List[float] = None) -> Optional[SetupSignal]:
        if len(closes) < 50:
            return None
        
        # Aumentamos a janela de resistência para 50 períodos para evitar ruído
        resistance = max(highs[-50:-1])
        support = min(lows[-50:-1])
        
        # Volume médio para confirmação
        avg_vol = sum(volumes[-20:]) / 20 if volumes else 1.0
        curr_vol = volumes[-1] if volumes else 1.0

        # GATILHO LONG: Rompimento com Volume (em vez de esperar 3 candles)
        if current_price > resistance and curr_vol > avg_vol * 1.5:
            return SetupSignal(
                setup_type="momentum_breakout",
                symbol="BTCUSDT",
                timeframe="5m",
                direction=TradeDirection.LONG,
                confidence=0.80,
                entry_price=current_price,
                stop_price=None,
                reason=f"Rompimento de resistência (50p) com Volume {curr_vol/avg_vol:.1f}x acima da média"
            )

        # GATILHO SHORT: Rompimento de suporte com Volume
        if current_price < support and curr_vol > avg_vol * 1.5:
            return SetupSignal(
                setup_type="momentum_breakout",
                symbol="BTCUSDT",
                timeframe="5m",
                direction=TradeDirection.SHORT,
                confidence=0.80,
                entry_price=current_price,
                stop_price=None,
                reason=f"Rompimento de suporte (50p) com Volume {curr_vol/avg_vol:.1f}x acima da média"
            )
        
        return None

    def detect_mean_reversion(self, closes: List[float], highs: List[float],
                              lows: List[float], current_price: float) -> Optional[SetupSignal]:
        if len(closes) < 20:
            return None
        
        rsi_curr = Indicators.calculate_rsi(closes, 14)
        rsi_prev = Indicators.calculate_rsi(closes[:-1], 14)
        ema_200 = Indicators.calculate_ema(closes, 200)
        
        # GATILHO LONG: RSI saindo da zona de sobrevenda (Oversold Hook)
        # Só operamos a favor da tendência principal (EMA 200)
        if rsi_prev < 30 and rsi_curr >= 30 and current_price > ema_200:
            return SetupSignal(
                setup_type="mean_reversion",
                symbol="BTCUSDT",
                timeframe="5m",
                direction=TradeDirection.LONG,
                confidence=0.75,
                entry_price=current_price,
                stop_price=None,
                reason=f"RSI Hook: Saiu de {rsi_prev:.0f} para {rsi_curr:.0f} acima da EMA200"
            )

        # GATILHO SHORT: RSI saindo da zona de sobrecompra (Overbought Hook)
        if rsi_prev > 70 and rsi_curr <= 70 and current_price < ema_200:
            return SetupSignal(
                setup_type="mean_reversion",
                symbol="BTCUSDT",
                timeframe="5m",
                direction=TradeDirection.SHORT,
                confidence=0.75,
                entry_price=current_price,
                stop_price=None,
                reason=f"RSI Hook: Saiu de {rsi_prev:.0f} para {rsi_curr:.0f} abaixo da EMA200"
            )
        
        return None

    def detect_breakout(self, closes, highs, lows, current_price, volumes=None) -> Optional[SetupSignal]:
        if len(closes) < 50 or not volumes:
            return None
        
        # Filtro de Volatilidade (Squeeze)
        # Comparamos o ATR atual com o de 50 períodos atrás
        atr_now = sum([highs[i]-lows[i] for i in range(-10, 0)]) / 10
        atr_base = sum([highs[i]-lows[i] for i in range(-50, -10)]) / 40
        
        vol_ratio = volumes[-1] / (sum(volumes[-20:]) / 20)
        ema_200 = Indicators.calculate_ema(closes, 200)

        # Se a volatilidade está "espremida" (Squeeze) e entra volume, é um breakout forte
        if atr_now < atr_base * 0.8 and vol_ratio > 2.0:
            squeeze_high = max(highs[-10:])
            squeeze_low = min(lows[-10:])

            if current_price > squeeze_high and current_price > ema_200:
                return SetupSignal(
                    setup_type="volatility_breakout",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.LONG,
                    confidence=0.85,
                    entry_price=current_price,
                    stop_price=None,
                    reason=f"Volatility Squeeze + Volume Spike ({vol_ratio:.1f}x)"
                )

            if current_price < squeeze_low and current_price < ema_200:
                return SetupSignal(
                    setup_type="volatility_breakout",
                    symbol="BTCUSDT",
                    timeframe="5m",
                    direction=TradeDirection.SHORT,
                    confidence=0.85,
                    entry_price=current_price,
                    stop_price=None,
                    reason=f"Volatility Squeeze + Volume Spike ({vol_ratio:.1f}x)"
                )

        return None
    
    def detect_all_setups(self, closes: List[float], highs: List[float],
                         lows: List[float], current_price: float) -> List[SetupSignal]:
        signals = []
        
        momentum = self.detect_momentum(closes, highs, lows, current_price)
        if momentum:
            signals.append(momentum)
        
        mean_rev = self.detect_mean_reversion(closes, highs, lows, current_price)
        if mean_rev:
            signals.append(mean_rev)
        
        breakout = self.detect_breakout(closes, highs, lows, current_price)
        if breakout:
            signals.append(breakout)
        
        signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return signals
    
    def __call__(self, candles) -> Optional[TradeDirection]:
        if len(candles) < self.min_bars_for_analysis:
            return None
        
        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]

        volumes = [c.volume for c in candles] if hasattr(candles[0], 'volume') else None
        
        current_price = closes[-1]

        brk = self.detect_breakout(closes, highs, lows, current_price, volumes)
        if brk: return brk.direction
        
        mrev = self.detect_mean_reversion(closes, highs, lows, current_price)
        if mrev: return mrev.direction
        
        mom = self.detect_momentum(closes, highs, lows, current_price)
        if mom: return mom.direction
        
        return None


class SetupValidator:    
    @staticmethod
    def validate_setup_signal(signal: SetupSignal, min_confidence: float = 0.50,
                             min_rr: float = 1.5) -> tuple:
        pontos = 0
        motivos = []
        
        if signal.confidence < min_confidence:
            return False, 0, f"Confiança baixa: {signal.confidence:.0%} (min: {min_confidence:.0%})"
        
        pontos += int(signal.confidence * 100)

        motivos.append(f"Setup: {signal.setup_type}")
        motivos.append(f"Confiança: {signal.confidence:.0%}")
        motivos.append(f"Razão: {signal.reason}")
        
        return True, pontos, " | ".join(motivos)
