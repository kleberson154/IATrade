"""
StopLossCalculator - Centraliza o cálculo de Stop Loss
Remove duplicação de código em 3 arquivos diferentes
"""

from enum import Enum
from typing import Tuple

class TradeDirection(Enum):
    LONG = "LONG"
    SHORT = "SHORT"

class StopLossCalculator:
    """Calcula Stop Loss de forma centralizada e confiável"""
    
    def __init__(self, stop_distance_percent: float = 0.15):
        """
        Args:
            stop_distance_percent: Distância do stop em % (ex: 0.15 = 15%)
        """
        self.stop_distance_percent = stop_distance_percent
    
    def calculate(
        self,
        entry_price: float,
        direction: TradeDirection,
        atr: float = None,
        use_atr: bool = False,
        atr_multiplier: float = 2.0
    ) -> float:
        """
        Calcula o preço de Stop Loss
        
        Args:
            entry_price: Preço de entrada
            direction: LONG ou SHORT
            atr: Average True Range (volatilidade)
            use_atr: Se deve usar ATR ao invés de % fixo
            atr_multiplier: Multiplicador de ATR (ex: 2.0 = 2x ATR)
        
        Returns:
            Preço de Stop Loss
        
        Exemplos:
            LONG:  Entry = 42500, SL = 42500 - (42500 * 0.15) = 36125
            SHORT: Entry = 42500, SL = 42500 + (42500 * 0.15) = 48875
        """
        if use_atr and atr is not None:
            # Usar ATR para cálculo dinâmico
            if direction == TradeDirection.LONG:
                return entry_price - (atr * atr_multiplier)
            else:  # SHORT
                return entry_price + (atr * atr_multiplier)
        else:
            # Usar % fixo
            stop_distance = entry_price * (self.stop_distance_percent / 100)
            
            if direction == TradeDirection.LONG:
                return entry_price - stop_distance
            else:  # SHORT
                return entry_price + stop_distance
    
    def validate(
        self,
        entry_price: float,
        stop_loss: float,
        direction: TradeDirection
    ) -> Tuple[bool, str]:
        """
        Valida se o Stop Loss está correto geometricamente
        
        Args:
            entry_price: Preço de entrada
            stop_loss: Preço de stop loss
            direction: LONG ou SHORT
        
        Returns:
            (is_valid, mensagem_de_erro)
        """
        if direction == TradeDirection.LONG:
            if stop_loss >= entry_price:
                return False, f"LONG: SL ({stop_loss}) deve estar ABAIXO de entry ({entry_price})"
            if stop_loss < 0:
                return False, f"SL não pode ser negativo: {stop_loss}"
        else:  # SHORT
            if stop_loss <= entry_price:
                return False, f"SHORT: SL ({stop_loss}) deve estar ACIMA de entry ({entry_price})"
            if stop_loss < 0:
                return False, f"SL não pode ser negativo: {stop_loss}"
        
        return True, "OK"
    
    def get_stop_distance_in_usd(
        self,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Retorna a distância em USD entre entry e SL"""
        return abs(entry_price - stop_loss)
    
    def get_stop_distance_in_percent(
        self,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Retorna a distância em % entre entry e SL"""
        distance_usd = self.get_stop_distance_in_usd(entry_price, stop_loss)
        return (distance_usd / entry_price) * 100
