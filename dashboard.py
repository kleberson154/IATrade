"""
Dashboard - Monitora o bot e envia notificações periódicas via Telegram
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import signal
from dotenv import load_dotenv

from utils.telegram_notifier import TelegramNotifier
from utils.trade_tracker import TradeTracker

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
        log_file: str = "logs/bot_trades.log"
    ):
        """
        Args:
            update_interval: Intervalo de atualização em segundos (default: 2h)
            log_file: Arquivo de log de trades
        """
        self.update_interval = update_interval
        self.log_file = log_file
        
        # Inicializar componentes
        self.notifier = TelegramNotifier()
        self.tracker = TradeTracker(log_file)
        
        # Estado
        self.running = False
        self.last_update = datetime.now()
        self.trades_notified = set()  # IDs das trades já notificadas
        
        logger.info(f"Dashboard inicializado (intervalo: {update_interval}s)")
    
    async def check_new_trades(self) -> bool:
        """
        Verifica e envia notificações de novas trades
        
        Returns:
            True se alguma trade foi notificada
        """
        try:
            open_trades = self.tracker.get_open_trades()
            new_trades = [t for t in open_trades if t.trade_id not in self.trades_notified]
            
            if not new_trades:
                return False
            
            logger.info(f"Encontradas {len(new_trades)} novas trades")
            
            for trade in new_trades:
                # Preparar dados
                trade_data = {
                    'symbol': trade.symbol,
                    'direction': trade.direction,
                    'entry_price': trade.entry_price,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'position_size': trade.position_size,
                    'rr_ratio': trade.calculate_rr_ratio(),
                    'time': trade.entry_time
                }
                
                # Enviar notificação
                success = await self.notifier.send_trade_notification(trade_data)
                
                if success:
                    self.trades_notified.add(trade.trade_id)
                    logger.info(f"Notificação enviada para trade {trade.trade_id}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao verificar novas trades: {e}")
            return False
    
    async def send_periodic_report(self) -> bool:
        """
        Envia relatório periódico de estatísticas
        
        Returns:
            True se relatório foi enviado
        """
        try:
            # Buscar trades do período
            hours = self.update_interval / 3600  # converter segundos para horas
            period_trades = self.tracker.get_trades_in_period(int(hours) + 1)
            
            # Calcular estatísticas
            stats = self.tracker.calculate_stats(period_trades)
            stats['period'] = f"Últimas {int(hours)}h"
            
            if stats['total_trades'] == 0:
                logger.info("Nenhuma trade no período para relatório")
                return False
            
            # Enviar relatório
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
                'mode': os.getenv('BYBIT_MODE', 'demo'),
                'symbols': os.getenv('SYMBOLS', 'BTCUSDT')
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
    log_file = os.getenv('LOG_FILE', 'logs/bot_trades.log')
    
    dashboard = Dashboard(update_interval=update_interval, log_file=log_file)
    
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
