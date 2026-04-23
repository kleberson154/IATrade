"""
Trade Tracker - Rastreia trades e coleta estatísticas para dashboard
"""

import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import csv
from pathlib import Path

logger = logging.getLogger("TradeTracker")


@dataclass
class Trade:
    """Representa uma trade realizada"""
    trade_id: str
    symbol: str
    direction: str  # 'long' ou 'short'
    entry_price: float
    entry_time: str
    stop_loss: float
    take_profit: float
    position_size: float
    exit_price: float = 0.0
    exit_time: str = ""
    exit_reason: str = ""  # 'tp', 'sl', 'manual'
    pnl_usd: float = 0.0
    pnl_percent: float = 0.0
    status: str = "open"  # 'open', 'closed', 'error'
    
    def to_dict(self):
        return asdict(self)
    
    def is_closed(self):
        return self.status == "closed"
    
    def calculate_rr_ratio(self) -> float:
        """Calcula o Risk/Reward ratio"""
        if self.stop_loss == 0:
            return 0.0
        
        if self.direction == "long":
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:  # short
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit
        
        if risk == 0:
            return 0.0
        
        return abs(reward / risk)


class TradeTracker:
    """Rastreia trades e coleta estatísticas"""
    
    def __init__(self, log_file: str = "logs/bot_trades.log"):
        """
        Args:
            log_file: Arquivo de log de trades
        """
        self.log_file = log_file
        self.trades: List[Trade] = []
        
        # Criar diretório se não existir
        Path(os.path.dirname(log_file)).mkdir(parents=True, exist_ok=True)
        
        # Carregar trades existentes
        self._load_trades()
    
    def _load_trades(self):
        """Carrega trades do arquivo de log"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                trade = Trade(**data)
                                self.trades.append(trade)
                            except (json.JSONDecodeError, TypeError):
                                logger.warning(f"Erro ao parsear trade: {line}")
                logger.info(f"Carregadas {len(self.trades)} trades do arquivo")
        except Exception as e:
            logger.error(f"Erro ao carregar trades: {e}")
    
    def add_trade(self, trade: Trade) -> bool:
        """
        Adiciona uma nova trade
        
        Args:
            trade: Trade para adicionar
        
        Returns:
            True se adicionada com sucesso
        """
        try:
            self.trades.append(trade)
            
            # Salvar no arquivo
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(trade.to_dict()) + '\n')
            
            logger.info(f"Trade adicionada: {trade.trade_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar trade: {e}")
            return False
    
    def update_trade(self, trade_id: str, **kwargs) -> bool:
        """
        Atualiza uma trade existente
        
        Args:
            trade_id: ID da trade
            **kwargs: Campos a atualizar
        
        Returns:
            True se atualizada com sucesso
        """
        try:
            for trade in self.trades:
                if trade.trade_id == trade_id:
                    for key, value in kwargs.items():
                        if hasattr(trade, key):
                            setattr(trade, key, value)
                    
                    # Recalcular arquivo
                    self._save_all_trades()
                    logger.info(f"Trade atualizada: {trade_id}")
                    return True
            
            logger.warning(f"Trade não encontrada: {trade_id}")
            return False
        except Exception as e:
            logger.error(f"Erro ao atualizar trade: {e}")
            return False
    
    def _save_all_trades(self):
        """Salva todas as trades no arquivo"""
        try:
            with open(self.log_file, 'w') as f:
                for trade in self.trades:
                    f.write(json.dumps(trade.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Erro ao salvar trades: {e}")
    
    def get_trades_in_period(self, hours: int = 2) -> List[Trade]:
        """
        Retorna trades do período especificado
        
        Args:
            hours: Número de horas para retroagir
        
        Returns:
            Lista de trades do período
        """
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            period_trades = []
            
            for trade in self.trades:
                try:
                    entry_time = datetime.fromisoformat(trade.entry_time)
                    if entry_time >= cutoff:
                        period_trades.append(trade)
                except ValueError:
                    logger.warning(f"Erro ao parsear data: {trade.entry_time}")
            
            return period_trades
        except Exception as e:
            logger.error(f"Erro ao buscar trades do período: {e}")
            return []
    
    def calculate_stats(self, trades: List[Trade] = None) -> Dict:
        """
        Calcula estatísticas das trades
        
        Args:
            trades: Lista de trades (default: todas)
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            if trades is None:
                trades = self.trades
            
            if not trades:
                return {
                    'total_trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'rr_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'max_win': 0.0,
                    'max_loss': 0.0
                }
            
            # Filtrar apenas trades fechadas
            closed_trades = [t for t in trades if t.is_closed()]
            
            if not closed_trades:
                return {
                    'total_trades': len(trades),
                    'wins': 0,
                    'losses': 0,
                    'win_rate': 0.0,
                    'total_pnl': 0.0,
                    'avg_win': 0.0,
                    'avg_loss': 0.0,
                    'rr_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'max_win': 0.0,
                    'max_loss': 0.0
                }
            
            wins = [t for t in closed_trades if t.pnl_usd > 0]
            losses = [t for t in closed_trades if t.pnl_usd < 0]
            
            total_pnl = sum(t.pnl_usd for t in closed_trades)
            avg_win = sum(t.pnl_usd for t in wins) / len(wins) if wins else 0.0
            avg_loss = sum(t.pnl_usd for t in losses) / len(losses) if losses else 0.0
            
            # Calcular drawdown
            cumulative_pnl = 0
            peak = 0
            max_drawdown = 0
            for trade in closed_trades:
                cumulative_pnl += trade.pnl_usd
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # RR Ratio médio
            rr_ratios = [t.calculate_rr_ratio() for t in closed_trades]
            avg_rr_ratio = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0.0
            
            return {
                'total_trades': len(closed_trades),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': (len(wins) / len(closed_trades) * 100) if closed_trades else 0.0,
                'total_pnl': total_pnl,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'rr_ratio': avg_rr_ratio,
                'max_drawdown': max_drawdown,
                'max_win': max([t.pnl_usd for t in wins], default=0.0),
                'max_loss': min([t.pnl_usd for t in losses], default=0.0)
            }
        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}
    
    def export_to_csv(self, filename: str = "trades_export.csv"):
        """
        Exporta trades para CSV
        
        Args:
            filename: Nome do arquivo
        """
        try:
            Path("exports").mkdir(exist_ok=True)
            filepath = f"exports/{filename}"
            
            if not self.trades:
                logger.warning("Nenhuma trade para exportar")
                return
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.trades[0].to_dict().keys())
                writer.writeheader()
                for trade in self.trades:
                    writer.writerow(trade.to_dict())
            
            logger.info(f"Trades exportadas para {filepath}")
        except Exception as e:
            logger.error(f"Erro ao exportar trades: {e}")
    
    def get_open_trades(self) -> List[Trade]:
        """Retorna trades abertas"""
        return [t for t in self.trades if t.status == "open"]
    
    def get_closed_trades(self) -> List[Trade]:
        """Retorna trades fechadas"""
        return [t for t in self.trades if t.status == "closed"]


# Teste
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    tracker = TradeTracker()
    
    # Adicionar uma trade de teste
    test_trade = Trade(
        trade_id="test_001",
        symbol="BTCUSDT",
        direction="long",
        entry_price=45000.0,
        entry_time=datetime.now().isoformat(),
        stop_loss=44500.0,
        take_profit=46000.0,
        position_size=0.1,
        exit_price=46000.0,
        exit_time=datetime.now().isoformat(),
        exit_reason="tp",
        pnl_usd=100.0,
        pnl_percent=2.22,
        status="closed"
    )
    
    tracker.add_trade(test_trade)
    
    # Calcular stats
    stats = tracker.calculate_stats()
    print(f"Stats: {stats}")
