"""
Backtester - Simula o bot de trading com dados históricos reais
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path

from connectors.data_provider import CandleData, DataProvider
from core.stop_loss_calculator import StopLossCalculator, TradeDirection
from core.take_profit_calculator import TakeProfitCalculator

@dataclass
class BacktestTrade:
    """Representa uma trade executada durante backteste"""
    trade_id: str
    symbol: str
    direction: TradeDirection
    entry_price: float
    entry_time: int
    position_size: float
    stop_loss: float
    take_profits: List[float]
    
    exit_price: float = 0.0
    exit_time: int = 0
    exit_reason: str = ""
    pnl_usd: float = 0.0
    pnl_percent: float = 0.0
    
    def calculate_pnl(self):
        """Calcula o P&L da trade"""
        if self.direction == TradeDirection.LONG:
            self.pnl_usd = (self.exit_price - self.entry_price) * self.position_size
        else:  # SHORT
            self.pnl_usd = (self.entry_price - self.exit_price) * self.position_size
        
        self.pnl_percent = (self.pnl_usd / (self.entry_price * self.position_size)) * 100
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'direction': self.direction.value,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time,
            'position_size': self.position_size,
            'stop_loss': self.stop_loss,
            'take_profits': self.take_profits,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time,
            'exit_reason': self.exit_reason,
            'pnl_usd': self.pnl_usd,
            'pnl_percent': self.pnl_percent,
        }

@dataclass
class BacktestStats:
    """Estatísticas do backteste"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    total_pnl: float = 0.0
    expectancy: float = 0.0
    rr_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    def calculate(self, trades: List[BacktestTrade]):
        """Calcula estatísticas a partir das trades"""
        if not trades:
            return
        
        self.total_trades = len(trades)
        
        wins = [t for t in trades if t.pnl_usd > 0]
        losses = [t for t in trades if t.pnl_usd < 0]
        
        self.winning_trades = len(wins)
        self.losing_trades = len(losses)
        
        self.win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        self.avg_win = sum(t.pnl_usd for t in wins) / len(wins) if wins else 0
        self.avg_loss = sum(t.pnl_usd for t in losses) / len(losses) if losses else 0
        
        self.total_pnl = sum(t.pnl_usd for t in trades)
        
        # Expectancy: (Win% x Avg_Win) - (Loss% x abs(Avg_Loss))
        win_pct = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        loss_pct = self.losing_trades / self.total_trades if self.total_trades > 0 else 0
        self.expectancy = (win_pct * self.avg_win) - (loss_pct * abs(self.avg_loss))
        
        # Risk/Reward Ratio
        if self.avg_loss != 0:
            self.rr_ratio = abs(self.avg_win / self.avg_loss)
        
        # Drawdown
        cumulative_pnl = 0
        peak = 0
        for trade in trades:
            cumulative_pnl += trade.pnl_usd
            if cumulative_pnl > peak:
                peak = cumulative_pnl
            drawdown = peak - cumulative_pnl
            if drawdown > self.max_drawdown:
                self.max_drawdown = drawdown
    
    def __str__(self) -> str:
        return f"""
================================================================================
BACKTESTE RESULTADO
================================================================================
Total Trades:       {self.total_trades}
Wins:               {self.winning_trades}
Losses:             {self.losing_trades}
Win Rate:           {self.win_rate:.1f}%
Avg Win:            ${self.avg_win:.2f}
Avg Loss:           ${self.avg_loss:.2f}
Total PnL:          ${self.total_pnl:+.2f}
Expectancy:         ${self.expectancy:+.2f}
RR Ratio:           {self.rr_ratio:.2f}x
Max Drawdown:       ${self.max_drawdown:.2f}
================================================================================
        """

class Backtester:
    """Executa o backteste com dados históricos reais"""
    
    def __init__(
        self,
        data_provider: DataProvider,
        starting_balance: float = 100.0,
        risk_per_trade: float = 0.01
    ):
        self.data_provider = data_provider
        self.starting_balance = starting_balance
        self.risk_per_trade = risk_per_trade
        
        self.trades: List[BacktestTrade] = []
        self.stats = BacktestStats()
        
        self.sl_calculator = StopLossCalculator(stop_distance_percent=0.15)
        self.tp_calculator = TakeProfitCalculator()
    
    async def run(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "5",
        start_date: datetime = None,
        end_date: datetime = None,
        setup_detector = None
    ) -> BacktestStats:
        """
        Executa o backteste
        
        Args:
            symbol: Par a tradear
            interval: Intervalo de candles
            start_date: Data inicial
            end_date: Data final
            setup_detector: Função que detecta setups (retorna TradeDirection ou None)
        
        Returns:
            BacktestStats com resultado do backteste
        """
        print(f"\n[BACKTESTE] Iniciando backteste: {symbol} {interval}min")
        print(f"[BACKTESTE] Período: {start_date or 'início'} até {end_date or 'fim'}")
        
        # Obter candles
        if start_date and end_date:
            candles = self.data_provider.get_candles_for_period(symbol, interval, start_date, end_date)
        else:
            candles = self.data_provider.get_klines(symbol, interval, limit=500)
        
        if not candles:
            print("[ERRO] Nenhum candle obtido")
            return self.stats
        
        print(f"[BACKTESTE] Carregados {len(candles)} candles")
        
        # Simular cada candle
        for i, candle in enumerate(candles):
            # Detectar setup
            if setup_detector and i > 20:
                direction = setup_detector(candles[:i+1])
                
                if direction:
                    trade = self._create_trade(symbol, candle, direction)
                    self.trades.append(trade)
                    print(f"[TRADE] #{len(self.trades)}: {direction.value} @ ${candle.close:.2f}")
            
            # Verificar se trades ativas atingem TP ou SL
            self._update_active_trades(candle)
        
        # Calcular estatísticas
        for trade in self.trades:
            trade.calculate_pnl()
        
        self.stats.calculate(self.trades)
        print(self.stats)
        
        return self.stats
    
    def _create_trade(
        self,
        symbol: str,
        candle: CandleData,
        direction: TradeDirection
    ) -> BacktestTrade:
        """Cria uma nova trade"""
        entry_price = candle.close
        stop_loss = self.sl_calculator.calculate(entry_price, direction)
        tps = self.tp_calculator.calculate(entry_price, direction)
        
        # Calcular tamanho da posição
        stop_distance = abs(entry_price - stop_loss)
        risk_amount = self.starting_balance * self.risk_per_trade
        position_size = risk_amount / stop_distance
        
        trade = BacktestTrade(
            trade_id=f"{len(self.trades):04d}",
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_time=candle.timestamp,
            position_size=position_size,
            stop_loss=stop_loss,
            take_profits=[tp.price for tp in tps]
        )
        
        return trade
    
    def _update_active_trades(self, candle: CandleData):
        """Verifica se trades ativas atingem TP ou SL"""
        for trade in self.trades:
            if trade.exit_time > 0:
                continue  # Já foi fechada
            
            # Verificar SL
            if trade.direction == TradeDirection.LONG:
                if candle.low <= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_time = candle.timestamp
                    trade.exit_reason = "Stop Loss"
                    continue
            else:  # SHORT
                if candle.high >= trade.stop_loss:
                    trade.exit_price = trade.stop_loss
                    trade.exit_time = candle.timestamp
                    trade.exit_reason = "Stop Loss"
                    continue
            
            # Verificar TPs - fecha no primeiro atingido
            for i, tp_price in enumerate(trade.take_profits):
                if trade.direction == TradeDirection.LONG:
                    if candle.high >= tp_price:
                        trade.exit_price = tp_price
                        trade.exit_time = candle.timestamp
                        trade.exit_reason = f"TP{i+1}"
                        break
                else:  # SHORT
                    if candle.low <= tp_price:
                        trade.exit_price = tp_price
                        trade.exit_time = candle.timestamp
                        trade.exit_reason = f"TP{i+1}"
                        break
    
    def save_trades_to_csv(self, filename: str = "backteste_trades.csv"):
        """Salva trades em CSV"""
        import csv
        
        Path("logs").mkdir(exist_ok=True)
        filepath = f"logs/{filename}"
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'trade_id', 'symbol', 'direction', 'entry_price', 'entry_time',
                'position_size', 'stop_loss', 'take_profits', 'exit_price',
                'exit_time', 'exit_reason', 'pnl_usd', 'pnl_percent'
            ])
            writer.writeheader()
            for trade in self.trades:
                row = trade.to_dict()
                row['take_profits'] = ','.join(f"{tp:.2f}" for tp in row['take_profits'])
                writer.writerow(row)
        
        print(f"\n[OK] Trades salvas em {filepath}")
    
    def save_stats_to_json(self, filename: str = "backteste_stats.json"):
        """Salva estatísticas em JSON"""
        Path("logs").mkdir(exist_ok=True)
        filepath = f"logs/{filename}"
        
        stats_dict = {
            'total_trades': self.stats.total_trades,
            'winning_trades': self.stats.winning_trades,
            'losing_trades': self.stats.losing_trades,
            'win_rate': self.stats.win_rate,
            'avg_win': self.stats.avg_win,
            'avg_loss': self.stats.avg_loss,
            'total_pnl': self.stats.total_pnl,
            'expectancy': self.stats.expectancy,
            'rr_ratio': self.stats.rr_ratio,
            'max_drawdown': self.stats.max_drawdown,
        }
        
        with open(filepath, 'w') as f:
            json.dump(stats_dict, f, indent=2)
        
        print(f"[OK] Estatísticas salvas em {filepath}")
