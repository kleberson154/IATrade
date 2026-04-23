"""
Trading Bot Orchestrator
Coordena todos os agentes de IA para execução disciplinada
Ponto de entrada principal do sistema
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config.settings import (
    BYBIT_API_MODE, DRY_RUN, SYMBOL, TIMEFRAME, 
    TIMEFRAMES_FOR_ANALYSIS, MAX_TRADES_PER_DAY, TRACK_EXPECTANCY
)
from connectors.bybit_connector import BybitConnector
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.risk_management_agent import RiskManagementAgent
from agents.execution_agent import ExecutionAgent
from agents.performance_monitor_agent import PerformanceMonitorAgent
from utils.trade_journal import TradeJournal
from models.trade_models import Trade, TradeStatus


class TradingBot:
    """
    Orquestrador principal do bot de trading
    Coordena: Market Analysis → Risk Management → Execution → Performance Monitoring
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        
        self.logger.info("=" * 80)
        self.logger.info("[BOT] TRADING BOT INICIANDO")
        self.logger.info(f"Modo: {BYBIT_API_MODE.upper()} | DRY_RUN: {DRY_RUN} | Symbol: {SYMBOL}")
        self.logger.info("=" * 80)
        
        # Conecta com Bybit
        self.bybit = BybitConnector(mode=BYBIT_API_MODE)
        
        # Inicializa agentes
        self.market_agent = MarketAnalysisAgent()
        self.risk_agent = RiskManagementAgent()
        self.execution_agent = ExecutionAgent(self.bybit)
        self.performance_agent = PerformanceMonitorAgent()
        
        # Journal
        self.journal = TradeJournal()
        
        # Estado
        self.is_running = False
        self.trades_today = 0
        self.last_analysis_time = None
        
        self._print_startup_info()
    
    def _setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler('logs/trading_bot.log'),
                logging.StreamHandler()
            ]
        )
    
    def _print_startup_info(self):
        """Imprime informações de inicialização"""
        print(f"""
================================================================================
                    TRADING BOT - Artigo: 5-15m Markets
                                                                              
  Modo: {BYBIT_API_MODE.upper():40} | DRY_RUN: {str(DRY_RUN):5}          
  Symbol: {SYMBOL:36} | Timeframe: {TIMEFRAME:11}      
                                                                              
  Regras aplicadas:                                                           
  [OK] Position Sizing: (Account x Risk%) / Stop Distance                       
  [OK] Expectancy: E = W x R - (1-W)                                            
  [OK] RR Minimo: 1.5x                                                           
  [OK] Risco por trade: 1% da conta                                             
  [OK] Setups: Momentum, Mean Reversion, Breakouts                             
  [OK] Disciplina: Nunca aumentar size apos loss                                
                                                                              
  Agentes:                                                                    
  - Market Analysis (detecta setups)                                         
  - Risk Management (posicao, stops, TPs)                                    
  - Execution (executa com disciplina)                                       
  - Performance Monitor (rastreia expectancy)                                
                                                                              
  Proximos passos:                                                            
  1. Configurar API credentials (se necessario)                              
  2. Chamar bot.start() para iniciar o loop                                  
  3. Monitorar performance em tempo real                                     
                                                                              
================================================================================
        """)
    
    async def fetch_market_data(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Busca dados de mercado para análise"""
        try:
            klines = self.bybit.get_klines(symbol, timeframe, limit=50)
            
            if not klines:
                # Em modo simulado, gera dados padrão
                self.logger.debug(f"klines vazio. is_simulated={self.bybit.is_simulated}")
                if self.bybit.is_simulated:
                    self.logger.debug("Usando dados simulados padrão")
                    klines = self.bybit._get_simulated_klines(symbol, timeframe, 50)
                    self.logger.debug(f"Gerados {len(klines)} candles")
                else:
                    self.logger.warning("Sem dados e não em modo simulado")
                    return None
            
            if not klines:
                self.logger.warning(f"Klines ainda vazio após fallback")
                return None
            
            # Processa klines: [time, open, high, low, close, volume, turnover]
            closes = [float(k[4]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            
            current_price = self.bybit.get_latest_price(symbol)
            
            result = {
                "closes": closes,
                "highs": highs,
                "lows": lows,
                "volumes": volumes,
                "current_price": current_price or closes[-1],
            }
            
            self.logger.debug(f"Dados de mercado retornados: {len(closes)} candles, preço={result['current_price']}")
            return result
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados: {e}", exc_info=True)
            return None
    
    async def analyze_market(self) -> Optional[Dict]:
        """Executa análise de mercado através do agente"""
        try:
            # Busca dados
            candle_data = await self.fetch_market_data(SYMBOL, TIMEFRAME)
            if not candle_data:
                self.logger.warning("Dados de mercado indisponíveis")
                return None
            
            # Análise primária
            analysis = self.market_agent.analyze_candle_data(candle_data)
            
            # Multi-timeframe (se aplicável)
            multi_tf_analysis = {}
            for tf in TIMEFRAMES_FOR_ANALYSIS:
                tf_data = await self.fetch_market_data(SYMBOL, tf)
                if tf_data:
                    multi_tf_analysis[tf] = self.market_agent.analyze_candle_data(tf_data)
            
            if multi_tf_analysis:
                analysis["multi_timeframe"] = self.market_agent.get_multi_timeframe_confirmation(
                    multi_tf_analysis
                )
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Erro na análise: {e}")
            return None
    
    async def check_trading_conditions(self) -> bool:
        """Valida condições para trading"""
        # Limite de trades por dia
        if self.trades_today >= MAX_TRADES_PER_DAY:
            self.logger.warning(f"Limite de trades ({MAX_TRADES_PER_DAY}) atingido hoje")
            return False
        
        # Verifica se deve pausar após losses
        should_pause, reason = self.risk_agent.should_pause_trading()
        if should_pause:
            self.logger.warning(f"Trading pausado: {reason}")
            return False
        
        # Mercado aberto?
        market_status = self.market_agent.get_trading_hours_status()
        if not market_status["trading_allowed"]:
            self.logger.warning("Mercado fechado")
            return False
        
        return True
    
    async def execute_trading_cycle(self) -> Optional[Trade]:
        """Ciclo completo de uma oportunidade de trade"""
        try:
            # Passo 1: Análise de mercado
            analysis = await self.analyze_market()
            if not analysis:
                return None
            
            # Tem sinal?
            signal = analysis.get("best_signal")
            if not signal:
                return None
            
            self.logger.info(f"Sinal detectado: {signal}")
            
            # Passo 2: Risk Management calcula posição
            candle_data = await self.fetch_market_data(SYMBOL, TIMEFRAME)
            volatility = analysis.get("volatility_analysis", {})
            
            trade = self.risk_agent.calculate_trade_setup(
                signal, 
                candle_data or {},
                volatility
            )
            
            if not trade:
                self.logger.warning("Falha ao calcular setup da trade")
                return None
            
            # Passo 3: Valida risco
            is_valid, message = self.risk_agent.validate_trade_risk(trade)
            
            if not is_valid:
                self.logger.warning(f"Trade rejeitada: {message}")
                return None
            
            self.logger.info(f"Trade aprovada: {self.risk_agent.get_position_summary(trade)}")
            
            # Passo 4: Execução
            exec_success, exec_msg = self.execution_agent.execute_trade(trade)
            
            if not exec_success:
                self.logger.error(f"Falha na execução: {exec_msg}")
                return None
            
            # Passo 5: Registros
            self.risk_agent.record_trade_execution(trade)
            self.journal.record_trade(trade)
            self.trades_today += 1
            
            return trade
        
        except Exception as e:
            self.logger.error(f"Erro no ciclo de trading: {e}", exc_info=True)
            return None
    
    def process_closed_trades(self):
        """Processa trades fechadas para performance monitoring"""
        open_trades = self.execution_agent.monitor_open_trades()
        
        for trade_id, trade in open_trades.get("trades", {}).items():
            # Simula fechamento em demo
            if trade.status == TradeStatus.OPEN:
                # Aqui verificaria condições de saída (SL, TP, etc)
                pass
    
    def print_performance_summary(self):
        """Imprime resumo de performance"""
        print("\n" + "=" * 80)
        print("PERFORMANCE MONITOR")
        print("=" * 80)
        
        print(self.performance_agent.get_performance_summary())
        
        if self.performance_agent.should_review_system():
            print("\n[ATENÇÃO] SYSTEM REVIEW NEEDED:")
            print(self.performance_agent.get_review_recommendation())
        
        print("\n" + "=" * 80)
    
    def print_agent_status(self):
        """Imprime status de todos os agentes"""
        print("\n" + "-" * 80)
        print("👥 AGENT STATUS")
        print("-" * 80)
        print(f"{self.market_agent.get_agent_status()}")
        print(f"{self.risk_agent.get_agent_status()}")
        print(f"{self.execution_agent.get_agent_status()}")
        print(f"{self.performance_agent.get_agent_status()}")
        print(f"Journal: {self.journal.get_summary()}")
        print("-" * 80 + "\n")
    
    async def start_trading_loop(self, interval_seconds: int = 5):
        """Loop principal de trading"""
        self.is_running = True
        self.logger.info(f"Iniciando trading loop (intervalo: {interval_seconds}s)")
        
        try:
            while self.is_running:
                try:
                    # Verifica condições
                    can_trade = await self.check_trading_conditions()
                    
                    if can_trade:
                        # Executa ciclo
                        trade = await self.execute_trading_cycle()
                        
                        if trade:
                            self.print_agent_status()
                    
                    # Processa trades fechadas
                    self.process_closed_trades()
                    
                    # Aguarda próximo intervalo
                    await asyncio.sleep(interval_seconds)
                
                except KeyboardInterrupt:
                    self.logger.info("⏹️ Parado pelo usuário")
                    break
                
                except Exception as e:
                    self.logger.error(f"Erro no loop: {e}", exc_info=True)
                    await asyncio.sleep(interval_seconds)
        
        finally:
            self.stop()
    
    def stop(self):
        """Para o bot gracefully"""
        self.is_running = False
        self.logger.info("🛑 Bot parado")
        self.print_performance_summary()
    
    async def backtest_simulation(self, num_cycles: int = 10):
        """Simula trades para teste"""
        self.logger.info(f"Iniciando simulação com {num_cycles} ciclos")
        
        for i in range(num_cycles):
            self.logger.info(f"\n--- Ciclo {i+1}/{num_cycles} ---")
            
            trade = await self.execute_trading_cycle()
            
            if trade:
                # Simula resultado
                import random
                is_win = random.random() < 0.55  # 55% win rate simulado
                
                if is_win:
                    trade.pnl_usdt = random.uniform(10, 50)
                    trade.pnl_percent = (trade.pnl_usdt / 1000) * 100
                else:
                    trade.pnl_usdt = -random.uniform(5, 30)
                    trade.pnl_percent = (trade.pnl_usdt / 1000) * 100
                
                trade.status = TradeStatus.CLOSED
                trade.close_time = datetime.utcnow()
                
                self.performance_agent.add_closed_trade(trade)
                self.risk_agent.record_trade_result(trade)
            
            await asyncio.sleep(0.5)
        
        self.print_performance_summary()
    
    def get_status(self) -> str:
        """Retorna status geral do bot"""
        return f"""
Bot Status:
- Rodando: {self.is_running}
- Trades hoje: {self.trades_today}/{MAX_TRADES_PER_DAY}
- {self.journal.get_summary()}
        """


# ============== ENTRY POINT ==============

def main():
    """Ponto de entrada"""
    bot = TradingBot()
    
    # Modo de teste
    print("\n[BOT] Escolha o modo:")
    print("1. Simulação (backtest 10 trades)")
    print("2. Live trading (DRY_RUN=True)")
    print("3. Status")
    
    choice = input("\nEscolha [1/2/3]: ").strip()
    
    if choice == "1":
        asyncio.run(bot.backtest_simulation(num_cycles=10))
    elif choice == "2":
        try:
            asyncio.run(bot.start_trading_loop(interval_seconds=5))
        except KeyboardInterrupt:
            print("\n⏹️ Parado")
    elif choice == "3":
        print(bot.get_status())
    else:
        print("Opção inválida")


if __name__ == "__main__":
    main()
