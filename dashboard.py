"""
Dashboard - Monitora o bot e envia notificações periódicas via Telegram
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import signal
from dotenv import load_dotenv

from connectors.bybit_connector import BybitConnector
from utils.telegram_notifier import TelegramNotifier

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(str(log_dir / 'dashboard.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Dashboard")


class Dashboard:
    """Dashboard que monitora o bot e envia notificações"""
    
    def __init__(
        self,
        update_interval: int = 7200,  # 2 horas em segundos
    ):
        """
        Args:
            update_interval: Intervalo de atualização em segundos (default: 2h)
        """
        self.update_interval = update_interval
        self.notifier = TelegramNotifier()
        self.connector = BybitConnector()
        self.symbol = os.getenv('SYMBOL', 'BTCUSDT')
        self.trade_history_start = self._resolve_trade_history_start()
        
        # Estado
        self.running = False
        self.last_update = datetime.now()
        self.trades_notified = set()  # IDs das trades já notificadas
        
        logger.info(f"Dashboard inicializado (intervalo: {update_interval}s)")
        logger.info(f"Dashboard vai buscar trades a partir de: {self.trade_history_start.isoformat()}")
    
    def _resolve_trade_history_start(self) -> datetime:
        """Resolve a data inicial para buscar histórico de trades usando variável de ambiente."""
        start_value = os.getenv("TRADE_HISTORY_START", "").strip()
        if start_value:
            for fmt in (
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
            ):
                try:
                    return datetime.strptime(start_value, fmt)
                except ValueError:
                    continue
            logger.warning(f"Formato inválido em TRADE_HISTORY_START: {start_value}. Usando 2h atrás.")
        return datetime.now() - timedelta(hours=2)
    
    def _fetch_trade_history(self) -> list:
        """Busca histórico de trades no Bybit e filtra por data de início."""
        trades = self.connector.get_trade_history(symbol=self.symbol, limit=100)
        filtered = []

        for trade in trades:
            exec_time = trade.get("execTime")
            if not exec_time:
                continue

            try:
                exec_dt = datetime.fromtimestamp(int(exec_time) / 1000)
            except Exception:
                continue

            if exec_dt >= self.trade_history_start:
                trade["_exec_dt"] = exec_dt
                filtered.append(trade)

        return sorted(filtered, key=lambda item: item["_exec_dt"])
    
    async def check_new_trades(self) -> bool:
        """
        Verifica e envia notificações de novas trades
        
        Returns:
            True se alguma trade foi notificada
        """
        try:
            trades = self._fetch_trade_history()
            new_trades = [t for t in trades if t.get("execId") not in self.trades_notified]
            
            if not new_trades:
                return False
            
            logger.info(f"Encontradas {len(new_trades)} novas trades na Bybit")
            
            for trade in new_trades:
                exec_id = trade.get("execId") or str(trade.get("orderId", "unknown"))
                direction = trade.get("side", "Buy").lower()
                entry_price = float(trade.get("execPrice", 0) or 0)
                entry_time = datetime.fromtimestamp(int(trade.get("execTime", 0)) / 1000).isoformat()

                trade_data = {
                    'symbol': trade.get('symbol', self.symbol),
                    'direction': direction,
                    'entry_price': entry_price,
                    'stop_loss': float(trade.get('stopLoss', 0) or 0),
                    'take_profit': float(trade.get('takeProfit', 0) or 0),
                    'position_size': float(trade.get('execQty', 0) or 0),
                    'rr_ratio': 0.0,
                    'time': entry_time
                }
                
                success = await self.notifier.send_trade_notification(trade_data)
                
                if success:
                    self.trades_notified.add(exec_id)
                    logger.info(f"Notificação enviada para trade {exec_id}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar novas trades: {e}")
            return False
    
    def _calculate_stats_from_history(self, trades: list) -> Dict:
        """Calcula estatísticas básicas do histórico de trades."""
        total = len(trades)
        buy_trades = sum(1 for t in trades if t.get('side', '').lower() == 'buy')
        sell_trades = sum(1 for t in trades if t.get('side', '').lower() == 'sell')
        total_quantity = sum(float(t.get('execQty', 0) or 0) for t in trades)

        return {
            'total_trades': total,
            'wins': 0,
            'losses': 0,
            'win_rate': 0.0,
            'total_pnl': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'rr_ratio': 0.0,
            'max_drawdown': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_quantity': total_quantity,
        }

    async def send_periodic_report(self) -> bool:
        """
        Envia relatório periódico de estatísticas
        
        Returns:
            True se relatório foi enviado
        """
        try:
            trades = self._fetch_trade_history()
            if not trades:
                logger.info("Nenhuma trade no período para relatório")
                return False
            
            stats = self._calculate_stats_from_history(trades)
            stats['period'] = f"Últimas {int(self.update_interval / 3600)}h"
            
            success = await self.notifier.send_stats_report(stats)
            
            if success:
                logger.info(f"Relatório enviado: {stats['total_trades']} trades")
            
            return success
        except Exception as e:
            logger.error(f"Erro ao enviar relatório periódico: {e}")
            return False
    
    async def monitor_loop(self):
        """Loop principal de monitoramento"""
        logger.info("Iniciando loop de monitoramento")
        
        try:
            while self.running:
                try:
                    # Verificar novas trades continuamente
                    await self.check_new_trades()
                    
                    # Enviar relatório periódico
                    time_since_update = (datetime.now() - self.last_update).total_seconds()
                    
                    if time_since_update >= self.update_interval:
                        logger.info("Enviando relatório periódico")
                        await self.send_periodic_report()
                        self.last_update = datetime.now()
                    
                    # Aguardar antes de próxima verificação (30 segundos)
                    await asyncio.sleep(30)
                
                except Exception as e:
                    logger.error(f"Erro no loop de monitoramento: {e}")
                    await asyncio.sleep(60)
        
        except asyncio.CancelledError:
            logger.info("Loop de monitoramento cancelado")
        finally:
            await self.shutdown()
    
    async def start(self):
        """Inicia o dashboard"""
        try:
            self.running = True
            logger.info("Dashboard iniciado")
            
            # Enviar mensagem de startup
            bot_info = {
                'version': '1.0.0',
                'mode': os.getenv('BYBIT_API_MODE', 'demo').upper(),
                'symbols': os.getenv('SYMBOL', 'BTCUSDT')
            }
            await self.notifier.send_startup_message(bot_info)
            
            # Iniciar loop de monitoramento
            await self.monitor_loop()
        
        except Exception as e:
            logger.error(f"Erro ao iniciar dashboard: {e}")
            await self.notifier.send_error_alert(str(e), "Dashboard Startup")
    
    async def shutdown(self):
        """Encerra o dashboard"""
        try:
            self.running = False
            logger.info("Dashboard encerrado")
            await self.notifier.send_message("🛑 Dashboard foi encerrado")
        except Exception as e:
            logger.error(f"Erro ao encerrar dashboard: {e}")


async def main():
    """Função principal"""
    
    # Criar dashboard
    update_interval = int(os.getenv('DASHBOARD_UPDATE_INTERVAL', 7200))
    
    dashboard = Dashboard(update_interval=update_interval)
    
    # Configurar tratamento de sinais para shutdown gracioso
    def signal_handler(sig, frame):
        logger.info(f"Sinal recebido: {sig}")
        dashboard.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar dashboard
    await dashboard.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dashboard interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
