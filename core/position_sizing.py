"""
Position Sizing - Onde contas vivem ou morrem
Fórmula: Position Size = (Account x Risk%) / Stop Distance

Importantíssimo: Mantém risco constante mesmo com volatilidade mudando
"""

from models.trade_models import PositionSize
from config.settings import ACCOUNT_SIZE_USDT, RISK_PER_TRADE_PERCENT


class PositionSizer:
    """Calcula tamanho da posição seguindo regras rígidas de risco"""
    
    def __init__(self, account_size: float = ACCOUNT_SIZE_USDT, 
                 risk_percent: float = RISK_PER_TRADE_PERCENT):
        self.account_size = account_size
        self.risk_percent = risk_percent
    
    def calculate_risk_amount(self) -> float:
        """
        Calcula quantidade em USD a arriscar nesta trade
        Risk Amount = Account Size x Risk%
        """
        return self.account_size * (self.risk_percent / 100)
    
    def calculate_position_size(self, entry_price: float, stop_loss_price: float) -> float:
        """
        Calcula quantidade de BTC a comprar/vender
        
        Fórmula do artigo:
        Position Size = (Account x Risk%) / Stop Distance
        
        Args:
            entry_price: preço de entrada
            stop_loss_price: preço do stop loss
        
        Returns:
            Quantidade em BTC (p.ex. 0.01 = 0.01 BTC)
        """
        risk_amount = self.calculate_risk_amount()
        stop_distance = abs(entry_price - stop_loss_price)
        
        if stop_distance == 0:
            raise ValueError("Stop distance não pode ser zero!")
        
        position_size = risk_amount / stop_distance
        
        return position_size
    
    def calculate_take_profits(self, entry_price: float, stop_loss_price: float,
                              rr_ratio: float = 1.5) -> dict:
        """
        Calcula take profits baseado em RR
        
        Multi-TP Strategy:
        - TP1 @ 50% do movimento esperado (close 50% da posição)
        - TP2 @ 75% do movimento esperado (close 30% da posição)  
        - TP3 @ 100% do movimento esperado (close 20% da posição)
        
        Args:
            entry_price: preço de entrada
            stop_loss_price: preço do stop
            rr_ratio: quantas vezes o reward vs risk (default: 1.5x)
        
        Returns:
            dict com tp1, tp2, tp3, rr_distance
        """
        stop_distance = abs(entry_price - stop_loss_price)
        rr_distance = stop_distance * rr_ratio
        
        # Determina direção
        if entry_price > stop_loss_price:  # LONG
            tp1 = entry_price + (rr_distance * 0.5)
            tp2 = entry_price + (rr_distance * 0.75)
            tp3 = entry_price + rr_distance
        else:  # SHORT
            tp1 = entry_price - (rr_distance * 0.5)
            tp2 = entry_price - (rr_distance * 0.75)
            tp3 = entry_price - rr_distance
        
        return {
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "rr_distance": rr_distance,
            "rr_ratio": rr_ratio,
        }
    
    def calculate_full_position(self, entry_price: float, stop_loss_price: float,
                               rr_ratio: float = 1.5) -> dict:
        """
        Calcula posição completa: size, risk, reward, TPs
        """
        position_size = self.calculate_position_size(entry_price, stop_loss_price)
        risk_amount = self.calculate_risk_amount()
        
        stop_distance = abs(entry_price - stop_loss_price)
        reward_distance = stop_distance * rr_ratio
        reward_amount = position_size * reward_distance
        
        tps = self.calculate_take_profits(entry_price, stop_loss_price, rr_ratio)
        
        return {
            "position_size": position_size,
            "entry_price": entry_price,
            "stop_loss": stop_loss_price,
            "risk_amount": risk_amount,
            "reward_amount": reward_amount,
            "rr_ratio": rr_ratio,
            "tp1": tps["tp1"],
            "tp2": tps["tp2"],
            "tp3": tps["tp3"],
            "stop_distance_pips": stop_distance,
            "reward_distance_pips": reward_distance,
        }
    
    def validate_rr_ratio(self, entry_price: float, stop_loss_price: float,
                         tp_price: float) -> tuple:
        """
        Valida se o RR está aceitável (mínimo 1.5x)
        
        Returns:
            (é_válido: bool, rr_atual: float, mensagem: str)
        """
        from config.settings import MIN_RR_RATIO
        
        stop_distance = abs(entry_price - stop_loss_price)
        reward_distance = abs(tp_price - entry_price)
        
        if stop_distance == 0:
            return False, 0, "Stop distance é zero"
        
        rr = reward_distance / stop_distance
        
        if rr >= MIN_RR_RATIO:
            return True, rr, f"RR válido: {rr:.2f}x (min: {MIN_RR_RATIO})"
        else:
            return False, rr, f"RR baixo: {rr:.2f}x (min: {MIN_RR_RATIO}x)"
    
    def scale_position_by_volatility(self, base_size: float, 
                                     volatility_adjustment: float) -> float:
        """
        Ajusta tamanho da posição por volatilidade
        Mantém risco constante em USD
        
        Args:
            base_size: tamanho calculado normalmente
            volatility_adjustment: fator de ajuste (0.75 = 25% menor, 1.25 = 25% maior)
        
        Returns:
            position_size ajustado
        """
        return base_size * volatility_adjustment
    
    def get_position_summary(self, calc_dict: dict) -> str:
        """Retorna resumo formatado da posição"""
        return (
            f"Position: {calc_dict['position_size']:.4f} BTC | "
            f"Entry: ${calc_dict['entry_price']:.2f} | "
            f"SL: ${calc_dict['stop_loss']:.2f} | "
            f"Risk: ${calc_dict['risk_amount']:.2f} | "
            f"Reward: ${calc_dict['reward_amount']:.2f} | "
            f"RR: {calc_dict['rr_ratio']:.2f}x"
        )
