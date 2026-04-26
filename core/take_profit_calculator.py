from typing import List, Tuple

from models.trade_models import TradeDirection

class TakeProfitLevel:
    def __init__(self, price: float, volume_percent: float, label: str):
        self.price = price
        self.volume_percent = volume_percent
        self.label = label
    
    def __repr__(self):
        return f"{self.label}(price={self.price:.2f}, vol={self.volume_percent*100:.0f}%)"

class TakeProfitCalculator:
    def __init__(
        self,
        tp_volumes: List[float] = [0.50, 0.30, 0.20]
    ):
        self.tp_volumes = tp_volumes
        if abs(sum(tp_volumes) - 1.0) > 0.01:
            raise ValueError("Os volumes dos TPs devem somar 1.0 (100%)")

    def calculate_adaptive_tps(
        self,
        entry_price: float,
        stop_loss: float,
        direction: TradeDirection
    ) -> List[TakeProfitLevel]:
        risk = abs(entry_price - stop_loss)
        
        multipliers = [1.0, 2.0, 3.5]
        labels = ["TP1", "TP2", "TP3"]
        tps = []

        for i, m in enumerate(multipliers):
            gain = risk * m
            if direction == TradeDirection.LONG:
                tp_price = entry_price + gain
            else:
                tp_price = entry_price - gain
            
            tps.append(TakeProfitLevel(
                price=tp_price, 
                volume_percent=self.tp_volumes[i],
                label=labels[i]
            ))
        
        return tps