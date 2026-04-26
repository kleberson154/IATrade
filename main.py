import multiprocessing
import os
import asyncio
import argparse
import logging
from connectors.bybit_connector import BybitConnector, BYBIT_API_MODE
from agents.execution_agent import ExecutionAgent
from agents.market_analysis_agent import MarketAnalysisAgent

class TradingBot:
    def __init__(self):
        self.bybit = BybitConnector(mode=BYBIT_API_MODE)
        self.execution_agent = ExecutionAgent(self.bybit)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("TradingBot")
        self.market_agent = MarketAnalysisAgent(agent_id="MA-PRO")
        self.is_running = False

    # --- FUNÇÕES DE TRADE ---
    
    async def analyze_market(self):
        symbol = "BTCUSDT"
        klines = self.bybit.get_klines(symbol="BTCUSDT", interval="15m", limit=200)
        
        if not klines:
            self.logger.error("Bybit retornou lista vazia!")
            return None

        # 2. Validação de quantidade mínima para os indicadores do Agente
        if len(klines) < 50: 
            self.logger.warning(f"Dados insuficientes: {len(klines)} velas. O agente precisa de 50.")
            return None
        
        try:
            last_price = float(klines[-1][4])
            
            # 3. Conversão para o formato do Agente
            formatted_data = {
                # Chaves no Plural
                "opens":   [float(k[1]) for k in klines],
                "highs":   [float(k[2]) for k in klines],
                "lows":    [float(k[3]) for k in klines],
                "closes":  [float(k[4]) for k in klines],
                "volumes": [float(k[5]) for k in klines],
                "current_price": last_price,
                
                # Chaves no Singular (A maioria dos agentes exige assim)
                "open":    [float(k[1]) for k in klines],
                "high":    [float(k[2]) for k in klines],
                "low":     [float(k[3]) for k in klines],
                "close":   [float(k[4]) for k in klines],
                "volume":  [float(k[5]) for k in klines],
                "current_price": last_price
            }
            
            # self.logger.info("=== DEBUG PAYLOAD ===")
            # self.logger.info(f"É um dicionário? {isinstance(formatted_data, dict)}")
            # self.logger.info(f"Chaves presentes: {list(formatted_data.keys())}")
            # self.logger.info(f"Qtd de velas (closes): {len(formatted_data['closes'])}")
            
            # 4. Análise (Agora garantimos que analysis só é chamada com dados bons)
            analysis = self.market_agent.analyze_candle_data(formatted_data)
            
            # 5. Verificação da recomendação
            recommendation = analysis.get("recommendation", "NONE")
            action = recommendation.get("action", "WAIT")
            
            if action == "CONSIDER_TRADE":
                self.logger.info("🔥 Sinal detectado pelo Agente!")

            if recommendation in ["STRONG_SETUP", "SETUP_CONFIRMED"]:
                self.logger.info(f"🔥 Setup detectado: {recommendation}")
                signal = self.market_agent.last_signal
                
                if signal:
                    return {
                        "best_signal": signal,
                        "symbol": symbol,
                        "confidence": analysis.get("confidence_score", 0)
                    }

        except Exception as e:
            self.logger.error(f"Erro no processamento da análise: {e}")
            
        return None

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
    from dashboard import main as dash_main
    asyncio.run(dash_main())

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