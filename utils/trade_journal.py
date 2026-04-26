"""
Trade Journal - Registra todas as trades para análise
Essencial para backtesting e aprendizado
"""

import logging
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from models.trade_models import Trade


class TradeJournal:
    """Gerencia journal de trades com múltiplos formatos"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # Arquivos de log
        self.csv_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        self.json_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        self.trades: List[Trade] = []
        self.is_breakeven = False
        self._init_csv()
    
    def _init_csv(self):
        """Cria arquivo CSV com headers"""
        headers = [
            "trade_id", "symbol", "direction", "setup_type",
            "entry_time", "entry_price", "entry_size",
            "stop_loss", "tp1", "tp2", "tp3",
            "close_time", "close_price", "exit_reason",
            "pnl_usdt", "pnl_percent", "rr_ratio",
            "status", "note"
        ]
        
        try:
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
        except Exception as e:
            self.logger.error(f"Erro ao criar CSV: {e}")
    
    def record_trade(self, trade: Trade):
        """Registra uma trade no journal"""
        self.trades.append(trade)
        
        # Escreve em CSV
        self._write_to_csv(trade)
        
        # Atualiza JSON
        self._write_to_json()
    
    def _write_to_csv(self, trade: Trade):
        """Escreve trade no CSV"""
        try:
            row = {
                "trade_id": trade.id,
                "symbol": trade.symbol,
                "direction": trade.direction.value,
                "setup_type": trade.setup_type,
                "entry_time": trade.entry_time.isoformat(),
                "entry_price": f"{trade.entry_price:.2f}",
                "entry_size": f"{trade.entry_size:.4f}",
                "stop_loss": f"{trade.stop_loss:.2f}",
                "tp1": f"{trade.tp1:.2f}",
                "tp2": f"{trade.tp2:.2f}",
                "tp3": f"{trade.tp3:.2f}",
                "close_time": trade.close_time.isoformat() if trade.close_time else "",
                "close_price": f"{trade.close_price:.2f}" if trade.close_price else "",
                "exit_reason": trade.exit_reason or "",
                "pnl_usdt": f"{trade.pnl_usdt:+.2f}",
                "pnl_percent": f"{trade.pnl_percent:+.2f}%",
                "rr_ratio": f"{trade.rr_ratio:.2f}",
                "status": trade.status.value,
                "note": trade.note,
            }
            
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writerow(row)
        
        except Exception as e:
            self.logger.error(f"Erro ao escrever CSV: {e}")
    
    def _write_to_json(self):
        """Escreve todas as trades em JSON"""
        try:
            data = []
            for trade in self.trades:
                data.append({
                    "id": trade.id,
                    "symbol": trade.symbol,
                    "direction": trade.direction.value,
                    "setup_type": trade.setup_type,
                    "entry": {
                        "price": trade.entry_price,
                        "size": trade.entry_size,
                        "time": trade.entry_time.isoformat(),
                    },
                    "exit": {
                        "price": trade.close_price,
                        "time": trade.close_time.isoformat() if trade.close_time else None,
                        "reason": trade.exit_reason,
                    },
                    "levels": {
                        "stop_loss": trade.stop_loss,
                        "tp1": trade.tp1,
                        "tp2": trade.tp2,
                        "tp3": trade.tp3,
                    },
                    "result": {
                        "pnl_usdt": trade.pnl_usdt,
                        "pnl_percent": trade.pnl_percent,
                        "rr_ratio": trade.rr_ratio,
                    },
                    "status": trade.status.value,
                    "note": trade.note,
                })
            
            with open(self.json_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Erro ao escrever JSON: {e}")
    
    def get_summary(self) -> str:
        """Retorna resumo das trades"""
        if not self.trades:
            return "Nenhuma trade registrada"
        
        closed_trades = [t for t in self.trades if t.is_closed]
        if not closed_trades:
            return f"{len(self.trades)} trades abertas"
        
        wins = len([t for t in closed_trades if t.is_profitable])
        losses = len([t for t in closed_trades if not t.is_profitable])
        total_pnl = sum([t.pnl_usdt for t in closed_trades])
        
        return (
            f"Trades: {len(closed_trades)} | "
            f"Wins: {wins} | Losses: {losses} | "
            f"Total PnL: ${total_pnl:+.2f}"
        )
    
    def get_journal_path(self) -> str:
        """Retorna path dos arquivos de journal"""
        return str(self.log_dir)
    
    def get_active_trade(self, symbol: str) -> Optional[Trade]:
        """Busca uma trade aberta para o símbolo específico"""
        for trade in self.trades:
            # Assume que status OPEN significa que a posição está rodando
            if trade.symbol == symbol and trade.status.value == "open":
                return trade
        return None

    def mark_as_breakeven(self, symbol: str):
        """Marca a trade como protegida em breakeven"""
        trade = self.get_active_trade(symbol)
        if trade:
            # Adicionamos uma nota ou atributo dinâmico
            trade.note = f"{trade.note} | [PROTECTED-BE]"
            # Se sua classe Trade tiver o atributo, melhor:
            if hasattr(trade, 'is_breakeven'):
                trade.is_breakeven = True
            
            self.logger.info(f"📓 Journal: Trade {symbol} marcada como Breakeven.")
            # Atualizamos os arquivos para refletir a mudança
            self._write_to_json()
