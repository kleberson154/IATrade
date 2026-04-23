"""
TakeProfitCalculator - Centraliza o cálculo de Take Profits
Remove duplicação de código em 2 arquivos diferentes
"""

from enum import Enum
from typing import List, Tuple

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class TakeProfitLevel:
    """Representa um nível de Take Profit"""
    
    def __init__(self, price: float, volume_percent: float):
        self.price = price
        self.volume_percent = volume_percent
    
    def __repr__(self):
        return f"TP(price={self.price:.2f}, vol={self.volume_percent*100:.0f}%)"

class TakeProfitCalculator:
    """Calcula Take Profits de forma centralizada e confiável"""
    
    def __init__(
        self,
        tp1_gain_percent: float = 0.5,
        tp2_gain_percent: float = 1.0,
        tp3_gain_percent: float = 1.5,
        tp1_volume_percent: float = 0.50,
        tp2_volume_percent: float = 0.30,
        tp3_volume_percent: float = 0.20
    ):
        """
        Args:
            tp*_gain_percent: Lucro % para cada TP
            tp*_volume_percent: % da posição a vender em cada TP
        """
        self.tp1_gain_percent = tp1_gain_percent
        self.tp2_gain_percent = tp2_gain_percent
        self.tp3_gain_percent = tp3_gain_percent
        
        self.tp1_volume_percent = tp1_volume_percent
        self.tp2_volume_percent = tp2_volume_percent
        self.tp3_volume_percent = tp3_volume_percent
        
        # Validar que volumes somam 100%
        total_volume = tp1_volume_percent + tp2_volume_percent + tp3_volume_percent
        if abs(total_volume - 1.0) > 0.01:
            raise ValueError(f"Volumes devem somar 100%, total: {total_volume*100:.1f}%")
    
    def calculate(
        self,
        entry_price: float,
        direction: TradeDirection,
        custom_tp_gains: List[float] = None
    ) -> List[TakeProfitLevel]:
        """
        Calcula os 3 níveis de Take Profit
        
        Args:
            entry_price: Preço de entrada
            direction: LONG ou SHORT
            custom_tp_gains: Valores customizados [tp1%, tp2%, tp3%] (opcional)
        
        Returns:
            Lista com 3 TakeProfitLevel
        
        Exemplos:
            LONG Entry 42500, TP1=0.5%:   42500 + (42500 * 0.005) = 42712.50
            SHORT Entry 42500, TP1=0.5%:  42500 - (42500 * 0.005) = 42287.50
        """
        if custom_tp_gains:
            gains = custom_tp_gains
        else:
            gains = [self.tp1_gain_percent, self.tp2_gain_percent, self.tp3_gain_percent]
        
        tps = []
        for i, gain in enumerate(gains):
            gain_amount = entry_price * (gain / 100)
            
            if direction == TradeDirection.LONG:
                tp_price = entry_price + gain_amount
            else:  # SHORT
                tp_price = entry_price - gain_amount
            
            # Volumes distribuídos
            volumes = [self.tp1_volume_percent, self.tp2_volume_percent, self.tp3_volume_percent]
            tps.append(TakeProfitLevel(tp_price, volumes[i]))
        
        return tps
    
    def validate(
        self,
        entry_price: float,
        tp_prices: List[float],
        direction: TradeDirection
    ) -> Tuple[bool, str]:
        """
        Valida se os TPs estão corretos geometricamente
        
        Args:
            entry_price: Preço de entrada
            tp_prices: Lista com preços dos TPs
            direction: LONG ou SHORT
        
        Returns:
            (is_valid, mensagem_de_erro)
        """
        if len(tp_prices) != 3:
            return False, f"Deve ter 3 TPs, recebido {len(tp_prices)}"
        
        if direction == TradeDirection.LONG:
            # LONG: TP1 < TP2 < TP3, todos > entry
            if not (entry_price < tp_prices[0] < tp_prices[1] < tp_prices[2]):
                return False, f"LONG: Entry({entry_price}) < TP1({tp_prices[0]}) < TP2({tp_prices[1]}) < TP3({tp_prices[2]})"
        else:  # SHORT
            # SHORT: TP1 > TP2 > TP3, todos < entry
            if not (entry_price > tp_prices[0] > tp_prices[1] > tp_prices[2]):
                return False, f"SHORT: Entry({entry_price}) > TP1({tp_prices[0]}) > TP2({tp_prices[1]}) > TP3({tp_prices[2]})"
        
        return True, "OK"
    
    def get_profit_at_tp(
        self,
        entry_price: float,
        tp_price: float,
        position_size_btc: float
    ) -> float:
        """
        Calcula lucro em USD ao atingir um TP
        
        Args:
            entry_price: Preço de entrada em USD
            tp_price: Preço do TP em USD
            position_size_btc: Tamanho da posição em BTC
        
        Returns:
            Lucro em USD
        """
        price_gain = tp_price - entry_price
        return price_gain * position_size_btc
    
    def get_expected_profit(
        self,
        entry_price: float,
        direction: TradeDirection,
        position_size_btc: float,
        tp_gains: List[float] = None
    ) -> Tuple[float, float]:
        """
        Calcula o lucro esperado considerando todos os TPs
        
        Args:
            entry_price: Preço de entrada
            direction: LONG ou SHORT
            position_size_btc: Tamanho da posição
            tp_gains: Valores customizados de TP (opcional)
        
        Returns:
            (total_profit_usd, profit_percent)
        """
        tps = self.calculate(entry_price, direction, tp_gains)
        
        total_profit = 0
        for tp in tps:
            profit_at_tp = self.get_profit_at_tp(entry_price, tp.price, position_size_btc)
            profit_at_tp_with_volume = profit_at_tp * tp.volume_percent
            total_profit += profit_at_tp_with_volume
        
        profit_percent = (total_profit / (entry_price * position_size_btc)) * 100
        
        return total_profit, profit_percent
