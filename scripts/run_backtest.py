#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_backtest.py - Executa backteste com dados históricos reais
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import logging

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.backtester import Backtester
from connectors.data_provider import HistoricalDataProvider, SimulatedDataProvider
from core.setup_detector import SetupDetector
from core.stop_loss_calculator import TradeDirection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Backtester")

class BacktestRunner:
    """Orquestra a execução do backteste"""
    
    def __init__(self, data_file: str = None):
        """
        Args:
            data_file: Caminho do arquivo com dados históricos (CSV ou JSON)
        """
        if data_file and Path(data_file).exists():
            logger.info(f"Carregando dados de {data_file}")
            self.data_provider = HistoricalDataProvider(data_file)
        else:
            logger.warning("Arquivo de dados não encontrado, usando simulador")
            self.data_provider = SimulatedDataProvider()
        
        self.detector = SetupDetector()
        self.backtester = Backtester(self.data_provider, starting_balance=100.0)
    
    async def run(self):
        """Executa o backteste"""
        logger.info("="*80)
        logger.info("BACKTESTE COM DADOS HISTÓRICOS REAIS")
        logger.info("="*80)
        logger.info(f"Data: {datetime.now()}")
        logger.info(f"Provedor de dados: {type(self.data_provider).__name__}")
        logger.info("="*80)
        
        # Detector de setups
        def detect_setup(candles):
            if len(candles) < 20:
                return None
            
            closes = [c.close for c in candles]
            highs = [c.high for c in candles]
            lows = [c.low for c in candles]
            current_price = candles[-1].close
            
            # Tentar detectar Mean Reversion
            signal = self.detector.detect_mean_reversion(closes, highs, lows, current_price)
            if signal:
                return signal.direction
            
            # Tentar detectar Momentum
            signal = self.detector.detect_momentum(closes, highs, lows, current_price)
            if signal:
                return signal.direction
            
            return None
        
        # Executar backteste
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        stats = await self.backtester.run(
            symbol="BTCUSDT",
            interval="5",
            start_date=start_date,
            end_date=end_date,
            setup_detector=detect_setup
        )
        
        # Salvar resultados
        self.backtester.save_trades_to_csv("backteste_resultado_real.csv")
        self.backtester.save_stats_to_json("backteste_stats_real.json")
        
        logger.info("\n" + str(stats))
        
        return stats

async def main():
    """Função principal"""
    
    # Verificar se existe arquivo de dados
    data_file = "data/btc_5min_90d.csv"
    
    if not Path(data_file).exists():
        logger.error("="*80)
        logger.error("ARQUIVO DE DADOS NÃO ENCONTRADO!")
        logger.error("="*80)
        logger.error(f"\nPor favor, execute primeiro:")
        logger.error(f"  python scripts/download_historical_data.py")
        logger.error(f"\nIsso irá baixar dados do Bitcoin dos últimos 90 dias")
        logger.error(f"e salvar em: {data_file}")
        logger.error("="*80)
        return None
    
    # Executar backteste
    runner = BacktestRunner(data_file)
    stats = await runner.run()
    
    return stats

if __name__ == "__main__":
    try:
        stats = asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("\n[CANCELADO] Backteste interrompido")
    except Exception as e:
        logger.error(f"\n[ERRO] {e}", exc_info=True)
