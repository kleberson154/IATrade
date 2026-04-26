import numpy as np
from typing import List

class Indicators:
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        if down == 0: return 100.0
        rs = up / down
        for i in range(period, len(deltas)):
            delta = deltas[i]
            up_val, down_val = (delta, 0.0) if delta > 0 else (0.0, -delta)
            up = (up * (period - 1) + up_val) / period
            down = (down * (period - 1) + down_val) / period
        rs = up / down if down != 0 else 0
        return 100. - 100. / (1. + rs)

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        if len(prices) < period:
            return sum(prices) / len(prices)
        prices_array = np.array(prices)
        alpha = 2 / (period + 1)
        ema = np.mean(prices_array[:period])
        for price in prices_array[period:]:
            ema = (price - ema) * alpha + ema
        return ema
    
    @staticmethod
    def calculate_volume_spike(volumes: List[float], period: int = 20) -> float:
        """Retorna o ratio do volume atual vs média (ex: 2.0 significa dobro do volume)"""
        if len(volumes) < period:
            return 1.0
        avg_volume = sum(volumes[-period:]) / period
        return volumes[-1] / avg_volume if avg_volume > 0 else 1.0
    
    @staticmethod
    def calculate_poc(closes: List[float], volumes: List[float], bins: int = 20) -> float:
        """
        Calcula o Point of Control (POC) simplificado.
        bins: quantidade de faixas de preço para dividir o perfil.
        """
        if not closes or not volumes or len(closes) != len(volumes):
            return sum(closes) / len(closes) if closes else 0

        # Criamos as faixas de preço (bins) entre a mínima e a máxima do período
        price_min, price_max = min(closes), max(closes)
        if price_min == price_max: return price_min
        
        counts, bin_edges = np.histogram(closes, bins=bins, weights=volumes)
        
        # O POC é o centro da faixa (bin) que teve o maior volume acumulado
        max_volume_bin_index = np.argmax(counts)
        poc = (bin_edges[max_volume_bin_index] + bin_edges[max_volume_bin_index + 1]) / 2
        
        return float(poc)