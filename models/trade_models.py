"""
Modelos de dados para trades e análise
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import uuid


class TradeStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TradeDirection(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class PriceLevel:
    """Nível de preço com tipo"""
    price: float
    type: str  # "entry", "stop", "tp1", "tp2", "tp3"
    
    def __str__(self):
        return f"{self.type}={self.price:.2f}"


@dataclass
class Trade:
    """Modelo completo de uma trade"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = "BTCUSDT"
    direction: TradeDirection = TradeDirection.LONG
    setup_type: str = "momentum"  # momentum, mean_reversion, breakout
    
    entry_price: float = 0.0
    entry_time: datetime = field(default_factory=datetime.utcnow)
    entry_size: float = 0.0
    
    stop_loss: float = 0.0
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    
    status: TradeStatus = TradeStatus.PENDING
    close_price: Optional[float] = None
    close_time: Optional[datetime] = None
    
    # Resultados
    pnl_usdt: float = 0.0
    pnl_percent: float = 0.0
    exit_reason: Optional[str] = None  # "tp1", "tp2", "tp3", "sl", "manual"
    
    # Estatísticas
    risk_amount: float = 0.0
    reward_amount: float = 0.0
    rr_ratio: float = 0.0
    
    # Metadata
    note: str = ""
    
    @property
    def is_profitable(self) -> bool:
        """Trade foi lucrativa?"""
        return self.pnl_usdt > 0
    
    @property
    def is_closed(self) -> bool:
        """Trade foi fechada?"""
        return self.status == TradeStatus.CLOSED
    
    def calculate_expectancy(self) -> float:
        """
        Calcula expectancy: E = W x R - (1-W)
        Simplificado para uma trade: se ganhamos, E = reward_amount, se perdemos E = -risk_amount
        Em série, a expectancy real é: avg_win x win_rate - avg_loss x (1-win_rate)
        """
        if self.is_profitable:
            return self.pnl_usdt
        else:
            return -self.risk_amount
    
    def __str__(self):
        return (
            f"Trade {self.id} | {self.symbol} {self.direction.value.upper()} "
            f"| Entry: {self.entry_price:.2f} | Size: {self.entry_size:.4f} "
            f"| SL: {self.stop_loss:.2f} | TP1/2/3: {self.tp1:.2f}/{self.tp2:.2f}/{self.tp3:.2f} "
            f"| RR: {self.rr_ratio:.2f}x | Status: {self.status.value}"
        )


@dataclass
class VolatilityData:
    """Dados de volatilidade (ATR)"""
    symbol: str
    timeframe: str
    atr_value: float  # Valor absoluto do ATR
    atr_percent: float  # ATR como % do preço
    current_price: float
    high_volatility: bool  # True se ATR > threshold
    low_volatility: bool  # True se ATR < threshold
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SetupSignal:
    """Sinal de setup detectado"""
    setup_type: str  # momentum, mean_reversion, breakout
    symbol: str
    timeframe: str
    direction: TradeDirection
    confidence: float  # 0.0 a 1.0
    entry_price: float
    stop_price: float
    reason: str  # Descrição do setup
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __str__(self):
        return (
            f"{self.setup_type.upper()} {self.direction.value.upper()} | "
            f"Conf: {self.confidence:.0%} | Entry: {self.entry_price:.2f} | "
            f"SL: {self.stop_price:.2f}"
        )


@dataclass
class PositionSize:
    """Cálculo de tamanho de posição"""
    account_size: float
    risk_percent: float
    stop_distance: float  # Distância entre entry e stop em preço absoluto
    entry_price: float
    
    # Calculados
    risk_amount: float = 0.0
    position_size: float = 0.0
    
    def calculate(self):
        """
        Position Size = (Account x Risk%) / Stop Distance
        """
        self.risk_amount = self.account_size * self.risk_percent
        self.position_size = self.risk_amount / self.stop_distance
        return self


@dataclass
class PerformanceStats:
    """Estatísticas de performance"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    win_rate: float = 0.0  # W em E = W x R - (1-W)
    avg_win: float = 0.0
    avg_loss: float = 0.0
    rr_ratio: float = 0.0  # R em E = W x R - (1-W)
    
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    
    expectancy: float = 0.0  # E = W x R - (1-W)
    expectancy_percent: float = 0.0  # Em % do account
    
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_losses: int = 0
    max_consecutive_losses: int = 0
    
    profit_factor: float = 0.0  # gross_profit / abs(gross_loss)
    sharpe_ratio: float = 0.0
    
    def calculate(self, trades: List[Trade]):
        """Calcula todas as estatísticas"""
        if not trades:
            return
        
        self.total_trades = len(trades)
        closed_trades = [t for t in trades if t.is_closed]
        
        if not closed_trades:
            return
        
        wins = [t for t in closed_trades if t.is_profitable]
        losses = [t for t in closed_trades if not t.is_profitable]
        
        self.winning_trades = len(wins)
        self.losing_trades = len(losses)
        self.win_rate = self.winning_trades / len(closed_trades) if closed_trades else 0
        
        if wins:
            win_amounts = [t.pnl_usdt for t in wins]
            self.avg_win = sum(win_amounts) / len(wins)
            self.gross_profit = sum(win_amounts)
            self.largest_win = max(win_amounts)
        
        if losses:
            loss_amounts = [abs(t.pnl_usdt) for t in losses]
            self.avg_loss = sum(loss_amounts) / len(losses)
            self.gross_loss = -sum(loss_amounts)
            self.largest_loss = max(loss_amounts)
        
        # Expectancy: E = W x R - (1-W)
        # onde R = avg_win / avg_loss
        if self.avg_loss > 0:
            self.rr_ratio = self.avg_win / self.avg_loss
            self.expectancy = (self.win_rate * self.rr_ratio) - (1 - self.win_rate)
        
        self.total_pnl = sum([t.pnl_usdt for t in closed_trades])
        self.expectancy_percent = self.expectancy * 100
        
        if self.gross_loss != 0:
            self.profit_factor = self.gross_profit / abs(self.gross_loss)
    
    def __str__(self):
        return (
            f"Win Rate: {self.win_rate:.1%} | Avg Win: ${self.avg_win:.2f} | "
            f"Avg Loss: ${self.avg_loss:.2f} | RR: {self.rr_ratio:.2f}x | "
            f"Expectancy: {self.expectancy:.0%} | Total PnL: ${self.total_pnl:.2f}"
        )
