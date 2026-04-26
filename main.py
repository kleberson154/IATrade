import multiprocessing
import os
import asyncio
import argparse
from connectors.bybit_connector import BybitConnector, BYBIT_API_MODE
from agents.execution_agent import ExecutionAgent

class TradingBot:
    def __init__(self):
        self.bybit = BybitConnector(mode=BYBIT_API_MODE)
        self.execution_agent = ExecutionAgent(self.bybit)
        self.is_running = False

    # --- FUNÇÕES DE TRADE ---

    async def open_position(self, trade_setup):
        """Chama o agente de execução para abrir ordem na Bybit"""
        self.logger.info(f" tentando abrir {trade_setup.direction} em {trade_setup.symbol}")
        success, msg = self.execution_agent.execute_trade(trade_setup)
        if success:
            self.logger.info(f"✅ Ordem enviada: {msg}")
            return True
        else:
            self.logger.error(f"❌ Falha na execução: {msg}")
            return False

    async def manage_active_positions(self):
        """
        Lógica de 'Trailing Stop' ou 'Breakeven'.
        Roda a cada ciclo do bot para ajustar ordens abertas.
        """
        try:
            positions = self.bybit.get_open_positions()
            if not positions:
                return

            for pos in positions:
                # Aqui entra a lógica que você já tem de mover o Stop Loss
                # para o preço de entrada (Breakeven) após o TP1.
                symbol = pos.get('symbol')
                current_price = await self.bybit.get_latest_price(symbol)
                
                # Exemplo: Se lucro > X, move Stop
                # self.bybit.set_trading_stop(...)
                pass
        except Exception as e:
            self.logger.error(f"Erro no monitoramento de posições: {e}")

    async def start_trading_loop(self, interval_seconds: int = 5):
        """O coração do Bot que a Oracle vai rodar 24h"""
        self.is_running = True
        while self.is_running:
            try:
                # 1. Analisa Mercado
                analysis = await self.analyze_market()
                
                # 2. Verifica Sinal e Executa
                if analysis and analysis.get("best_signal"):
                    # Calcula risco e abre trade
                    setup = self.risk_agent.calculate_trade_setup(analysis["best_signal"])
                    if setup:
                        await self.open_position(setup)

                # 3. Gerencia o que já está aberto
                await self.manage_active_positions()

                await asyncio.sleep(interval_seconds)
            except Exception as e:
                self.logger.error(f"Erro no loop principal: {e}")
                await asyncio.sleep(10)

# --- WRAPPERS PARA MULTIPROCESSING ---

def run_bot_process(interval):
    bot = TradingBot()
    asyncio.run(bot.start_trading_loop(interval_seconds=interval))

def run_dash_process():
    from dashboard import run_dashboard
    run_dashboard()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["bot", "dash", "all"], default="all")
    args = parser.parse_args()

    processes = []

    if args.mode in ["all", "bot"]:
        p = multiprocessing.Process(target=run_bot_process, args=(5,), name="BotTrader")
        p.start()
        processes.append(p)

    if args.mode in ["all", "dash"]:
        p = multiprocessing.Process(target=run_dash_process, name="Dashboard")
        p.start()
        processes.append(p)

    try:
        for p in processes: p.join()
    except KeyboardInterrupt:
        for p in processes: p.terminate()