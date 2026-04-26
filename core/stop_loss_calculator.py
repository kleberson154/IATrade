from typing import Tuple

from models.trade_models import TradeDirection

class StopLossCalculator:
    def __init__(self, stop_distance_percent: float = 1.5):
        self.stop_distance_percent = stop_distance_percent
    
    def calculate(
        self,
        entry_price: float,
        direction: TradeDirection,
        atr: float = None,
        use_atr: bool = False,
        atr_multiplier: float = 2.0
    ) -> float:
        if use_atr and atr is not None:
            distance = atr * atr_multiplier
        else:
            distance = entry_price * (self.stop_distance_percent / 100)

        if direction == TradeDirection.LONG:
            sl_price = entry_price - distance
            return min(sl_price, entry_price * 0.999) 
        else:  # SHORT
            sl_price = entry_price + distance
            return max(sl_price, entry_price * 1.001)
    
    def validate(
        self,
        entry_price: float,
        stop_loss: float,
        direction: TradeDirection
    ) -> Tuple[bool, str]:
        if direction == TradeDirection.LONG:
            if stop_loss >= entry_price:
                return False, f"LONG: SL ({stop_loss}) deve estar ABAIXO de entry ({entry_price})"
            if stop_loss < 0:
                return False, f"SL não pode ser negativo: {stop_loss}"
        else:
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
        return abs(entry_price - stop_loss)
    
    def get_stop_distance_in_percent(
        self,
        entry_price: float,
        stop_loss: float
    ) -> float:
        distance_usd = self.get_stop_distance_in_usd(entry_price, stop_loss)
        return (distance_usd / entry_price) * 100
