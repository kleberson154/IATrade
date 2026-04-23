"""
Telegram Notifier - Envia notificações e relatórios via Telegram
"""

import os
import logging
from typing import Dict, Optional, List
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger("TelegramNotifier")


class TelegramNotifier:
    """Envia mensagens e notificações via Telegram"""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self, token: str = None, chat_id: str = None):
        """
        Args:
            token: Token do bot Telegram (default: env TELEGRAM_TOKEN)
            chat_id: ID do chat (default: env TELEGRAM_CHAT_ID)
        """
        self.token = token or os.getenv("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token or not self.chat_id:
            raise ValueError("TELEGRAM_TOKEN e TELEGRAM_CHAT_ID são obrigatórios")
        
        self.api_url = f"{self.BASE_URL}{self.token}"
        logger.info(f"TelegramNotifier inicializado para chat {self.chat_id}")
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Envia mensagem simples
        
        Args:
            text: Texto da mensagem
            parse_mode: HTML ou Markdown
        
        Returns:
            True se enviado com sucesso
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/sendMessage", json=payload) as resp:
                    if resp.status == 200:
                        logger.debug(f"Mensagem enviada com sucesso")
                        return True
                    else:
                        logger.error(f"Erro ao enviar mensagem: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False
    
    async def send_trade_notification(self, trade_data: Dict) -> bool:
        """
        Envia notificação de nova trade
        
        Args:
            trade_data: Dicionário com informações da trade
                {
                    'symbol': 'BTCUSDT',
                    'direction': 'long',
                    'entry_price': 45000.0,
                    'stop_loss': 44500.0,
                    'take_profit': 46000.0,
                    'position_size': 0.1,
                    'time': '2024-01-20 15:30:00'
                }
        
        Returns:
            True se enviado com sucesso
        """
        try:
            emoji_dir = "📈" if trade_data.get('direction') == 'long' else "📉"
            
            message = f"""
{emoji_dir} <b>NOVA TRADE</b>

<b>Símbolo:</b> {trade_data.get('symbol', 'N/A')}
<b>Direção:</b> {trade_data.get('direction', 'N/A').upper()}
<b>Entrada:</b> ${trade_data.get('entry_price', 0):.2f}
<b>Stop Loss:</b> ${trade_data.get('stop_loss', 0):.2f}
<b>Take Profit:</b> ${trade_data.get('take_profit', 0):.2f}
<b>Tamanho:</b> {trade_data.get('position_size', 0):.4f}
<b>Risco/Recompensa:</b> 1:{trade_data.get('rr_ratio', 0):.2f}
<b>Hora:</b> {trade_data.get('time', 'N/A')}
            """.strip()
            
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de trade: {e}")
            return False
    
    async def send_stats_report(self, stats: Dict) -> bool:
        """
        Envia relatório de estatísticas do bot
        
        Args:
            stats: Dicionário com estatísticas
                {
                    'total_trades': 100,
                    'wins': 60,
                    'losses': 40,
                    'win_rate': 60.0,
                    'total_pnl': 1000.0,
                    'avg_win': 50.0,
                    'avg_loss': -25.0,
                    'rr_ratio': 2.0,
                    'period': '2 horas'
                }
        
        Returns:
            True se enviado com sucesso
        """
        try:
            win_rate = stats.get('win_rate', 0)
            pnl = stats.get('total_pnl', 0)
            
            emoji_pnl = "💰" if pnl >= 0 else "📉"
            color_pnl = "+" if pnl >= 0 else ""
            
            message = f"""
📊 <b>RELATÓRIO DE ESTATÍSTICAS</b>

<b>Período:</b> {stats.get('period', 'Últimas 2h')}
<b>Total de Trades:</b> {stats.get('total_trades', 0)}
<b>Ganhadoras:</b> {stats.get('wins', 0)} ✅
<b>Perdedoras:</b> {stats.get('losses', 0)} ❌
<b>Taxa de Acerto:</b> {win_rate:.1f}%

{emoji_pnl} <b>P&L TOTAL:</b> <b>{color_pnl}${pnl:,.2f}</b>
<b>Lucro Médio:</b> ${stats.get('avg_win', 0):.2f}
<b>Perda Média:</b> ${stats.get('avg_loss', 0):.2f}
<b>Razão R/R:</b> {stats.get('rr_ratio', 0):.2f}x
<b>Max Drawdown:</b> ${stats.get('max_drawdown', 0):.2f}

⏰ Atualizado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"Erro ao enviar relatório: {e}")
            return False
    
    async def send_error_alert(self, error_msg: str, context: str = "") -> bool:
        """
        Envia alerta de erro
        
        Args:
            error_msg: Mensagem de erro
            context: Contexto do erro
        
        Returns:
            True se enviado com sucesso
        """
        try:
            message = f"""
⚠️ <b>ALERTA DE ERRO</b>

<b>Contexto:</b> {context}
<b>Erro:</b> <code>{error_msg}</code>
<b>Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """.strip()
            
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"Erro ao enviar alerta: {e}")
            return False
    
    async def send_startup_message(self, bot_info: Dict = None) -> bool:
        """
        Envia mensagem de inicialização do bot
        
        Args:
            bot_info: Informações do bot
        
        Returns:
            True se enviado com sucesso
        """
        try:
            info = bot_info or {}
            message = f"""
🚀 <b>BOT INICIADO</b>

<b>Versão:</b> {info.get('version', '1.0.0')}
<b>Modo:</b> {info.get('mode', 'demo').upper()}
<b>Símbolos:</b> {info.get('symbols', 'N/A')}
<b>Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ Sistema pronto para operações
            """.strip()
            
            return await self.send_message(message)
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de inicialização: {e}")
            return False


# Função de teste
async def test_telegram():
    """Testa conexão com Telegram"""
    try:
        notifier = TelegramNotifier()
        
        # Teste 1: Mensagem simples
        print("Enviando mensagem de teste...")
        result = await notifier.send_message("✅ Teste de conexão bem-sucedido!")
        print(f"Resultado: {result}")
        
        # Teste 2: Notificação de trade
        print("\nEnviando notificação de trade...")
        trade_test = {
            'symbol': 'BTCUSDT',
            'direction': 'long',
            'entry_price': 45000.0,
            'stop_loss': 44500.0,
            'take_profit': 46000.0,
            'position_size': 0.1,
            'rr_ratio': 2.0,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        result = await notifier.send_trade_notification(trade_test)
        print(f"Resultado: {result}")
        
        # Teste 3: Relatório
        print("\nEnviando relatório...")
        stats_test = {
            'total_trades': 10,
            'wins': 7,
            'losses': 3,
            'win_rate': 70.0,
            'total_pnl': 500.0,
            'avg_win': 100.0,
            'avg_loss': -50.0,
            'rr_ratio': 2.0,
            'max_drawdown': 150.0,
            'period': 'Últimas 2 horas'
        }
        result = await notifier.send_stats_report(stats_test)
        print(f"Resultado: {result}")
        
    except Exception as e:
        print(f"Erro no teste: {e}")


if __name__ == "__main__":
    asyncio.run(test_telegram())
