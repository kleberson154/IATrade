"""
Backtester - Simula o bot de trading com dados históricos reais
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import json
from pathlib import Path

from connectors.data_provider import CandleData, DataProvider
from core.stop_loss_calculator import StopLossCalculator
from core.take_profit_calculator import TakeProfitCalculator
from models.trade_models import TradeDirection

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
    is_protected: bool = False
    hit_tps: Set[int] = field(default_factory=set)
    
    exit_price: float = 0.0
    exit_time: int = 0
    exit_reason: str = ""
    pnl_usd: float = 0.0
    pnl_percent: float = 0.0
    
    def calculate_pnl(self):
        if self.exit_price == 0: # Trade ainda aberta ou bugada
            self.pnl_usd = 0
            self.pnl_percent = 0
            return
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
        
        self.active_trade: Optional[BacktestTrade] = None
        
        self.sl_calculator = StopLossCalculator(stop_distance_percent=2.5)
        self.tp_calculator = TakeProfitCalculator()
    
    async def run(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "5",
        start_date: datetime = None,
        end_date: datetime = None,
        setup_detector = None,
        last_exit_index = -100
    ) -> BacktestStats:
        # Se não passar data, define os últimos 90 dias
        if not start_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
        elif not end_date:
            end_date = datetime.now()

        print(f"\n[BACKTESTE] Iniciando período de 90 dias: {symbol} {interval}min")
        print(f"[BACKTESTE] {start_date.strftime('%d/%m/%Y')} -> {end_date.strftime('%d/%m/%Y')}")
        
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
            if self.active_trade is not None:
                self._update_active_trades(candle)
                if self.active_trade is None:
                    last_exit_index = i
                    continue
                
            if i < last_exit_index + 12:
                continue
            
            if setup_detector and i > 20 and self.active_trade is None:
                direction = setup_detector(candles[max(0, i-200):i+1])
                if direction:
                    self.active_trade = self._create_trade(symbol, candle, direction)
                    self.trades.append(self.active_trade)
                    print(f"[TRADE] #{len(self.trades)}: {direction.value} @ ${candle.close:.2f}")
        
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
        
        if abs(entry_price - stop_loss) < (entry_price * 0.001): # Mínimo 0.1% de distância
            # Força um stop mínimo para o backtest não bugar
            dist = entry_price * 0.005 # 0.5%
            stop_loss = entry_price - dist if direction == TradeDirection.LONG else entry_price + dist
        
        tps = self.tp_calculator.calculate_adaptive_tps(
            entry_price=entry_price, 
            stop_loss=stop_loss, 
            direction=direction
        )
        
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
        
        trade.hit_tps = set()
        
        return trade
    
    def _update_active_trades(self, candle: CandleData):
        if not self.active_trade:
            return
        
        trade = self.active_trade
        
        if not hasattr(trade, 'hit_tps'):
            trade.hit_tps = set()
        
        # --- SEÇÃO 1: ATUALIZAÇÃO DE ESTADO E PROTEÇÃO ---
        for i, tp_price in enumerate(trade.take_profits):
            tp_level = i + 1
            
            # Lógica corrigida: verifica a condição baseada na direção
            if trade.direction == TradeDirection.LONG:
                hit_this_tp = candle.high >= tp_price
            else: # SHORT
                hit_this_tp = candle.low <= tp_price

            if hit_this_tp and tp_level not in trade.hit_tps:
                trade.hit_tps.add(tp_level)
                
                # Mover para Breakeven apenas no TP2
                if tp_level == 2:
                    trade.stop_loss = trade.entry_price
                    trade.is_protected = True
                    print(f"[PROTECTION] TP2 atingido. Stop em Breakeven: {trade.stop_loss}")

                # Se for o ÚLTIMO TP da lista, fecha a trade agora
                if tp_level == len(trade.take_profits):
                    self._close_trade(trade, candle, tp_price, f"TP{tp_level}")
                    return # Sai da função, a trade acabou

        # --- SEÇÃO 2: VERIFICAÇÃO DE STOP LOSS ---
        # Só chegamos aqui se a trade NÃO foi fechada pelo TP final acima
        exit_sl = False
        if trade.direction == TradeDirection.LONG:
            if candle.low <= trade.stop_loss:
                exit_sl = True
        else: # SHORT
            if candle.high >= trade.stop_loss:
                exit_sl = True

        if exit_sl:
            # Se o stop loss foi movido (is_protected), o motivo é "BREAKEVEN"
            reason = "BREAKEVEN" if trade.is_protected else "STOP_LOSS"
            self._close_trade(trade, candle, trade.stop_loss, reason)
            
    def _close_trade(self, trade, candle, exit_price, reason):
        trade.exit_price = exit_price
        trade.exit_time = candle.timestamp
        trade.exit_reason = reason

        if trade.direction == TradeDirection.LONG:
            pnl = (exit_price - trade.entry_price) * trade.position_size
        else:
            pnl = (trade.entry_price - exit_price) * trade.position_size

        self.active_trade = None
        
        print(f"[EXIT] {trade.direction.value.upper()} @ ${exit_price:.2f} | Razão: {reason} | PnL: ${pnl:.2f}")
    
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
    
    def log_benchmark(self, version_name: str):
        """Salva um resumo rápido para comparar versões do código"""
        log_path = Path("logs/benchmark_results.txt")
        with open(log_path, "a") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                    f"Versão: {version_name} | "
                    f"WinRate: {self.stats.win_rate:.1f}% | "
                    f"PnL: ${self.stats.total_pnl:.2f} | "
                    f"DD: ${self.stats.max_drawdown:.2f}\n")
