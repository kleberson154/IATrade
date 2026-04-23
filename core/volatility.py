"""
Calculador de Volatilidade (ATR)
Essencial para: Stop Loss dinâmico, Position Sizing adaptativo

Stop = Entry ± k x ATR
Em alta volatilidade: menor size
Em baixa volatilidade: maior size
"""

import numpy as np
from typing import List, Optional
from models.trade_models import VolatilityData
from config.settings import ATR_PERIOD, ATR_MULTIPLIER, ATR_HIGH_VOLATILITY_THRESHOLD, ATR_LOW_VOLATILITY_THRESHOLD


class VolatilityCalculator:
    """Calcula ATR e classifica nível de volatilidade"""
    
    def __init__(self, atr_period: int = ATR_PERIOD):
        self.atr_period = atr_period
        self.tr_values: List[float] = []
        self.atr_values: List[float] = []
    
    def calculate_true_range(self, high: float, low: float, close_prev: float) -> float:
        """
        True Range = max(
            high - low,
            abs(high - close_prev),
            abs(low - close_prev)
        )
        """
        tr = max(
            high - low,
            abs(high - close_prev),
            abs(low - close_prev)
        )
        return tr
    
    def calculate_atr(self, high_prices: List[float], low_prices: List[float], 
                     close_prices: List[float]) -> Optional[float]:
        """
        Calcula ATR usando SMA dos True Range values
        Precisa de no mínimo atr_period + 1 candles
        """
        if len(high_prices) < self.atr_period + 1:
            return None
        
        tr_values = []
        close_prev = close_prices[0]
        
        for i in range(len(high_prices)):
            if i == 0:
                continue
            
            high = high_prices[i]
            low = low_prices[i]
            tr = self.calculate_true_range(high, low, close_prev)
            tr_values.append(tr)
            close_prev = close_prices[i]
        
        if len(tr_values) < self.atr_period:
            return None
        
        # Usa SMA (média móvel simples)
        atr = sum(tr_values[-self.atr_period:]) / self.atr_period
        return atr
    
    def get_volatility_data(self, symbol: str, timeframe: str, 
                           current_price: float,
                           high_prices: List[float], low_prices: List[float],
                           close_prices: List[float]) -> Optional[VolatilityData]:
        """
        Calcula dados completos de volatilidade
        """
        atr = self.calculate_atr(high_prices, low_prices, close_prices)
        
        if atr is None:
            return None
        
        atr_percent = (atr / current_price) * 100
        
        high_vol = atr_percent > ATR_HIGH_VOLATILITY_THRESHOLD
        low_vol = atr_percent < ATR_LOW_VOLATILITY_THRESHOLD
        
        return VolatilityData(
            symbol=symbol,
            timeframe=timeframe,
            atr_value=atr,
            atr_percent=atr_percent,
            current_price=current_price,
            high_volatility=high_vol,
            low_volatility=low_vol
        )
    
    def calculate_stop_loss(self, entry_price: float, direction: str, atr: float, 
                           multiplier: float = ATR_MULTIPLIER) -> float:
        """
        Calcula stop loss dinâmico baseado em ATR
        Stop = Entry ± k x ATR
        
        Args:
            entry_price: preço de entrada
            direction: "long" ou "short"
            atr: valor do ATR
            multiplier: multiplicador (default: 2.0)
        """
        if direction.lower() == "long":
            stop = entry_price - (multiplier * atr)
        else:  # short
            stop = entry_price + (multiplier * atr)
        
        return stop
    
    def calculate_position_size_adjustment(self, atr_percent: float, 
                                          base_size: float) -> float:
        """
        Ajusta tamanho da posição baseado em volatilidade
        Alta volatilidade = menor size
        Baixa volatilidade = maior size
        
        Mantém o risco em USDT constante
        """
        if atr_percent > ATR_HIGH_VOLATILITY_THRESHOLD:
            # Alta volatilidade: reduz size em 25%
            return base_size * 0.75
        elif atr_percent < ATR_LOW_VOLATILITY_THRESHOLD:
            # Baixa volatilidade: aumenta size em 25%
            return base_size * 1.25
        else:
            # Volatilidade normal
            return base_size
    
    def get_volatility_regime(self, atr_percent: float) -> str:
        """Classifica o regime de volatilidade"""
        if atr_percent > ATR_HIGH_VOLATILITY_THRESHOLD:
            return "HIGH"
        elif atr_percent < ATR_LOW_VOLATILITY_THRESHOLD:
            return "LOW"
        else:
            return "NORMAL"


class VolatilityAnalyzer:
    """Analisa padrões de volatilidade ao longo do tempo"""
    
    def __init__(self, lookback_periods: int = 20):
        self.lookback_periods = lookback_periods
        self.volatility_history: List[float] = []
    
    def add_volatility(self, atr_percent: float):
        """Adiciona novo valor de volatilidade"""
        self.volatility_history.append(atr_percent)
        if len(self.volatility_history) > self.lookback_periods * 2:
            self.volatility_history = self.volatility_history[-self.lookback_periods * 2:]
    
    def get_average_volatility(self) -> Optional[float]:
        """Volatilidade média"""
        if not self.volatility_history:
            return None
        return sum(self.volatility_history) / len(self.volatility_history)
    
    def is_volatility_expanding(self) -> Optional[bool]:
        """Volatilidade está aumentando?"""
        if len(self.volatility_history) < 2:
            return None
        
        recent = sum(self.volatility_history[-5:]) / 5 if len(self.volatility_history) >= 5 else self.volatility_history[-1]
        older = sum(self.volatility_history[-10:-5]) / 5 if len(self.volatility_history) >= 10 else self.volatility_history[0]
        
        return recent > older
    
    def get_volatility_percentile(self, current_atr_percent: float) -> float:
        """Retorna em qual percentil está a volatilidade atual"""
        if not self.volatility_history:
            return 50.0
        
        sorted_vol = sorted(self.volatility_history)
        percentile = (sum(1 for v in sorted_vol if v <= current_atr_percent) / len(sorted_vol)) * 100
        return percentile
