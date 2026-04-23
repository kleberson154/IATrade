#!/usr/bin/env python3
"""
Script de Sincronização: Bybit Demo ↔ Histórico Local

Sincroniza automaticamente:
1. Ordens fechadas (closed orders) da Bybit
2. Histórico de execuções (trade history) da Bybit
3. Saldo da conta
4. Salva em arquivo JSON para auditoria

Uso:
    python sync_bybit_history.py
    python sync_bybit_history.py --symbol BTCUSDT
    python sync_bybit_history.py --full
"""

import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from connectors.bybit_connector import BybitConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SyncBybitHistory")


class BybitHistorySync:
    """Sincroniza histórico de trades com Bybit"""
    
    def __init__(self, output_dir: str = "logs"):
        self.connector = BybitConnector()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Arquivo de saída
        timestamp = datetime.now().strftime("%Y%m%d")
        self.sync_file = self.output_dir / f"bybit_sync_{timestamp}.json"
        self.sync_data = self._load_sync_file()
    
    def _load_sync_file(self) -> dict:
        """Carrega dados de sincronização anterior"""
        if self.sync_file.exists():
            try:
                with open(self.sync_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "sync_date": datetime.now().isoformat(),
            "account": {},
            "closed_orders": [],
            "trade_history": [],
            "stats": {}
        }
    
    def _save_sync_file(self):
        """Salva dados de sincronização"""
        with open(self.sync_file, 'w') as f:
            json.dump(self.sync_data, f, indent=2)
        logger.info(f"✅ Dados salvos em: {self.sync_file}")
    
    def sync_account_info(self):
        """Sincroniza informações da conta"""
        logger.info("📊 Sincronizando informações da conta...")
        
        account = self.connector.get_account_info()
        
        self.sync_data["account"] = {
            "wallet_balance": account.get("wallet_balance"),
            "available_balance": account.get("available_balance"),
            "used_margin": account.get("used_margin"),
            "sync_time": datetime.now().isoformat(),
        }
        
        logger.info(f"   Saldo: ${account.get('wallet_balance', 0)}")
        logger.info(f"   Disponível: ${account.get('available_balance', 0)}")
    
    def sync_closed_orders(self, symbol: str = None, limit: int = 100):
        """Sincroniza ordens fechadas"""
        logger.info(f"📋 Sincronizando closed orders {f'({symbol})' if symbol else '(todos)'}...")
        
        closed_orders = self.connector.get_closed_orders(symbol=symbol, limit=limit)
        
        logger.info(f"   Encontrado: {len(closed_orders)} ordens fechadas")
        
        # Agrupa por símbolo
        by_symbol = {}
        for order in closed_orders:
            sym = order.get("symbol", "UNKNOWN")
            if sym not in by_symbol:
                by_symbol[sym] = []
            by_symbol[sym].append(order)
        
        self.sync_data["closed_orders"] = closed_orders
        
        # Exibe resumo
        for sym, orders in by_symbol.items():
            buy_count = sum(1 for o in orders if o.get("side") == "Buy")
            sell_count = sum(1 for o in orders if o.get("side") == "Sell")
            logger.info(f"   {sym}: {buy_count} BUYs, {sell_count} SELLs")
    
    def sync_trade_history(self, symbol: str = None, limit: int = 100):
        """Sincroniza histórico de execução de trades"""
        logger.info(f"📈 Sincronizando trade history {f'({symbol})' if symbol else '(todos)'}...")
        
        trades = self.connector.get_trade_history(symbol=symbol, limit=limit)
        
        logger.info(f"   Encontrado: {len(trades)} execuções de trades")
        
        # Calcula estatísticas
        total_value = 0
        total_fees = 0
        by_side = {"Buy": 0, "Sell": 0}
        
        for trade in trades:
            side = trade.get("side", "Unknown")
            if side in by_side:
                by_side[side] += 1
            
            try:
                total_value += float(trade.get("execValue", 0))
                total_fees += float(trade.get("tradingFee", 0))
            except:
                pass
        
        self.sync_data["trade_history"] = trades
        self.sync_data["stats"] = {
            "total_trades": len(trades),
            "buy_trades": by_side["Buy"],
            "sell_trades": by_side["Sell"],
            "total_value": round(total_value, 2),
            "total_fees": round(total_fees, 4),
            "average_fee": round(total_fees / len(trades), 6) if trades else 0,
        }
        
        # Exibe resumo
        logger.info(f"   Buy: {by_side['Buy']}, Sell: {by_side['Sell']}")
        logger.info(f"   Valor Total: ${total_value:.2f}")
        logger.info(f"   Fees Totais: ${total_fees:.4f}")
    
    def sync_open_positions(self):
        """Sincroniza posições abertas"""
        logger.info("📍 Sincronizando posições abertas...")
        
        positions = self.connector.get_open_positions()
        
        logger.info(f"   Posições abertas: {len(positions)}")
        
        if positions:
            for pos in positions:
                symbol = pos.get("symbol", "UNKNOWN")
                size = pos.get("size", 0)
                pnl = pos.get("unrealisedPnl", 0)
                logger.info(f"   - {symbol}: {size} (PnL: ${pnl})")
    
    def generate_report(self):
        """Gera relatório de sincronização"""
        logger.info("\n" + "=" * 70)
        logger.info("RELATÓRIO DE SINCRONIZAÇÃO")
        logger.info("=" * 70)
        
        # Account
        account = self.sync_data.get("account", {})
        logger.info(f"\n💰 CONTA:")
        logger.info(f"   Saldo: ${account.get('wallet_balance', 0)}")
        logger.info(f"   Disponível: ${account.get('available_balance', 0)}")
        logger.info(f"   Margem Usada: ${account.get('used_margin', 0)}")
        
        # Stats
        stats = self.sync_data.get("stats", {})
        logger.info(f"\n📊 ESTATÍSTICAS:")
        logger.info(f"   Total de Trades: {stats.get('total_trades', 0)}")
        logger.info(f"   Buys: {stats.get('buy_trades', 0)}")
        logger.info(f"   Sells: {stats.get('sell_trades', 0)}")
        logger.info(f"   Valor Total: ${stats.get('total_value', 0):.2f}")
        logger.info(f"   Fees: ${stats.get('total_fees', 0):.4f}")
        logger.info(f"   Fee Média: ${stats.get('average_fee', 0):.6f}")
        
        # Closed Orders
        closed = self.sync_data.get("closed_orders", [])
        logger.info(f"\n📋 ORDENS FECHADAS:")
        logger.info(f"   Total: {len(closed)}")
        
        if closed:
            by_status = {}
            for order in closed:
                status = order.get("status", "UNKNOWN")
                by_status[status] = by_status.get(status, 0) + 1
            
            for status, count in by_status.items():
                logger.info(f"   - {status}: {count}")
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✅ Sincronização concluída!")
        logger.info(f"📁 Arquivo: {self.sync_file}")
        logger.info("=" * 70 + "\n")
    
    def sync_full(self, symbol: str = None):
        """Sincronização completa"""
        logger.info("\n🔄 INICIANDO SINCRONIZAÇÃO COMPLETA")
        logger.info("=" * 70)
        
        try:
            self.sync_account_info()
            self.sync_closed_orders(symbol=symbol, limit=100)
            self.sync_trade_history(symbol=symbol, limit=100)
            self.sync_open_positions()
            
            self._save_sync_file()
            self.generate_report()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro durante sincronização: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza histórico de trades com Bybit Demo"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Símbolo específico (ex: BTCUSDT)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Sincronização completa (padrão)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="logs",
        help="Diretório de saída (padrão: logs)"
    )
    
    args = parser.parse_args()
    
    # Inicializa sincronizador
    syncer = BybitHistorySync(output_dir=args.output_dir)
    
    # Executa sincronização
    success = syncer.sync_full(symbol=args.symbol)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
