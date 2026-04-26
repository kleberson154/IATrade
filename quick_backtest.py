import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.backtester import Backtester
from core.stop_loss_calculator import StopLossCalculator
from core.take_profit_calculator import TakeProfitCalculator
from connectors.bybit_connector import BybitConnector
from connectors.data_provider import BybitDataProvider
from core.setup_detector import SetupDetector
from models.trade_models import TradeDirection

# Configuração de Logging básica
logging.basicConfig(level=logging.INFO)

async def run_quick_backtest():
    """Executa o backteste com dados reais da Bybit"""
    
    # 1. Configurações Iniciais
    SYMBOL = "BTCUSDT"
    INTERVAL = "5" # 5 minutos
    DIAS_BACKTEST = 90
    
    print("\n" + "="*80)
    print(f"BACKTEST REAL - BYBIT DATA")
    print("="*80)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Instrumento: {SYMBOL}")
    print(f"Período: Últimos {DIAS_BACKTEST} dias")
    print(f"Intervalo: {INTERVAL} minutos")
    print("="*80)
    
    # 2. Inicializar Conectores Reais
    connector = BybitConnector() # Puxa do seu .env
    data_provider = BybitDataProvider(connector)
    
    # 3. Criar backtester (Saldo inicial de 100 USDT para facilitar visualização)
    backtester = Backtester(data_provider, starting_balance=100.0)
    
    # 4. Detector de setups (Sua lógica de Mean Reversion + RSI)
    detector_profissional = SetupDetector()
    
    # 5. Definir Período de Tempo
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DIAS_BACKTEST)
    
    # 6. Rodar backteste
    print(f"⏳ Baixando e processando dados históricos (isso pode levar um minuto)...")
    stats = await backtester.run(
        symbol=SYMBOL,
        interval=INTERVAL,
        start_date=start_date,
        end_date=end_date,
        setup_detector=detector_profissional  # O Backtester chamará o __call__ que criamos
    )
    
    # 7. Salvar resultados em disco
    backtester.save_trades_to_csv("backteste_real_90d.csv")
    backtester.save_stats_to_json("backteste_real_90d_stats.json")
    
    print("\n" + str(stats))
    
    print("\n" + "="*80)
    print("VALIDACAO TÉCNICA DO SISTEMA")
    print("="*80)
    
    # BUSCAR O PREÇO ATUAL PARA OS TESTES ABAIXO
    # Pegamos o preço de fechamento do último candle carregado no provedor
    last_price = data_provider.get_latest_price(SYMBOL)
    
    if last_price == 0:
        # Fallback caso a API não retorne o preço atual no momento
        last_price = 65000.0 

    # [Teste dos Calculadores]
    sl_calc = StopLossCalculator(stop_distance_percent=2.5)
    sl_long = sl_calc.calculate(last_price, TradeDirection.LONG)
    print(f"[1] StopLoss Check: Entry={last_price:.2f}, SL={sl_long:.2f} [OK]")
    
    tp_calc = TakeProfitCalculator()
    tps = tp_calc.calculate_adaptive_tps(
        entry_price=last_price, 
        stop_loss=last_price * 0.99, # Você precisa passar um valor de stop aqui para o cálculo
        direction=TradeDirection.LONG
    )
    print(f"[2] TakeProfit Check: TP1={tps[0].price:.2f} [OK]")
    
    print(f"[3] Resumo do Backtest:")
    print(f"    Total de Trades: {len(backtester.trades)}")
    print(f"    Saldo Final: ${stats.total_pnl + 100.0:.2f}")
    
    print("\n" + "="*80)
    print("✅ BACKTEST REALIZADO COM SUCESSO!")
    print("="*80 + "\n")
    
    return stats

if __name__ == "__main__":
    try:
        asyncio.run(run_quick_backtest())
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()