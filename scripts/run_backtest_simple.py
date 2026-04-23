#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_backtest_simple.py - Backteste simples com todos os dados disponíveis
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# Adicionar projeto ao path - subir um nível do scripts
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.backtester import Backtester
from connectors.data_provider import HistoricalDataProvider
from core.setup_detector import SetupDetector
from core.stop_loss_calculator import TradeDirection

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Backtester")

class SimpleBacktestRunner:
    """Orquestra a execução do backteste com todos os dados"""
    
    def __init__(self, data_file: str):
        """Args: data_file - Caminho do arquivo com dados históricos"""
        logger.info(f"Carregando dados de {data_file}")
        self.data_provider = HistoricalDataProvider(data_file)
        self.detector = SetupDetector()
        self.backtester = Backtester(self.data_provider, starting_balance=100.0)
    
    async def run(self):
        """Executa o backteste"""
        logger.info("="*80)
        logger.info("BACKTESTE COM DADOS HISTORICOS REAIS - SIMPLES")
        logger.info("="*80)
        logger.info(f"Data: {datetime.now()}")
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
        
        # Obter todos os candles disponíveis
        candles = self.data_provider.get_klines("BTCUSDT", 5, limit=999999)
        
        if not candles:
            logger.error("ERRO: Nenhum candle obtido!")
            return None
        
        logger.info(f"[OK] Carregados {len(candles)} candles")
        logger.info(f"Periodo: {candles[0].time_str} ate {candles[-1].time_str}")
        logger.info("")
        
        # Simular cada candle
        for i, candle in enumerate(candles):
            # Detectar setup
            if i > 20:
                direction = detect_setup(candles[:i+1])
                
                if direction:
                    trade = self.backtester._create_trade("BTCUSDT", candle, direction)
                    self.backtester.trades.append(trade)
                    logger.info(f"[TRADE] #{len(self.backtester.trades)}: {direction.value} @ ${candle.close:.2f}")
            
            # Verificar se trades ativas atingem TP ou SL
            self.backtester._update_active_trades(candle)
            
            # Log de progresso a cada 1000 candles
            if (i + 1) % 5000 == 0:
                logger.info(f"[PROGRESSO] {i+1}/{len(candles)} candles processados")
        
        # Calcular estatísticas
        for trade in self.backtester.trades:
            trade.calculate_pnl()
        
        self.backtester.stats.calculate(self.backtester.trades)
        logger.info(str(self.backtester.stats))
        
        # Salvar resultados
        self.backtester.save_trades_to_csv("backteste_resultado_real.csv")
        self.backtester.save_stats_to_json("backteste_stats_real.json")
        
        return self.backtester.stats

async def main():
    """Função principal"""
    
    # Verificar se existe arquivo de dados
    data_file = "data/btc_5min_90d.csv"
    
    if not Path(data_file).exists():
        logger.error("="*80)
        logger.error("ARQUIVO DE DADOS NAO ENCONTRADO!")
        logger.error("="*80)
        logger.error(f"\nPor favor, execute primeiro:")
        logger.error(f"  python scripts/download_historical_data.py")
        logger.error("="*80)
        return None
    
    # Executar backteste
    runner = SimpleBacktestRunner(data_file)
    stats = await runner.run()
    
    return stats

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("\n[CANCELADO] Backteste interrompido")
    except Exception as e:
        logger.error(f"\n[ERRO] {e}", exc_info=True)
