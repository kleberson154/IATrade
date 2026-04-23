"""
Exemplo: Como usar os agentes individuais
"""

import asyncio
from config.settings import BYBIT_API_MODE
from connectors.bybit_connector import BybitConnector
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.risk_management_agent import RiskManagementAgent
from core.position_sizing import PositionSizer
from core.volatility import VolatilityCalculator


async def example_market_analysis():
    """Exemplo 1: Análise de mercado"""
    print("=" * 80)
    print("EXEMPLO 1: Market Analysis")
    print("=" * 80)
    
    # Conecta com Bybit
    bybit = BybitConnector(mode=BYBIT_API_MODE)
    
    # Busca candles
    klines = bybit.get_klines("BTCUSDT", "5m", limit=50)
    print(f"Candles obtidos: {len(klines)}")
    
    if klines:
        # Processa candles
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        current_price = bybit.get_latest_price("BTCUSDT")
        
        # Analisa
        agent = MarketAnalysisAgent()
        analysis = agent.analyze_candle_data({
            "closes": closes,
            "highs": highs,
            "lows": lows,
            "current_price": current_price,
        })
        
        print(f"\nSinal detectado: {analysis.get('best_signal')}")
        print(f"Volatilidade: {analysis['volatility_analysis'].get('regime')}")


async def example_position_sizing():
    """Exemplo 2: Cálculo de position sizing"""
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Position Sizing")
    print("=" * 80)
    
    sizer = PositionSizer(account_size=1000, risk_percent=1.0)
    
    # Cenário: Entry @ 42500, Stop @ 42000
    entry = 42500
    stop = 42000
    
    # Calcula
    calc = sizer.calculate_full_position(entry, stop, rr_ratio=1.5)
    
    print(f"\nEntry: ${calc['entry_price']:.2f}")
    print(f"Stop: ${calc['stop_loss']:.2f}")
    print(f"Position: {calc['position_size']:.4f} BTC")
    print(f"Risk: ${calc['risk_amount']:.2f}")
    print(f"Reward: ${calc['reward_amount']:.2f}")
    print(f"RR: {calc['rr_ratio']:.2f}x")
    print(f"\nTP1: ${calc['tp1']:.2f} (50%)")
    print(f"TP2: ${calc['tp2']:.2f} (30%)")
    print(f"TP3: ${calc['tp3']:.2f} (20%)")


async def example_volatility():
    """Exemplo 3: Cálculo de volatilidade (ATR)"""
    print("\n" + "=" * 80)
    print("EXEMPLO 3: Volatility (ATR)")
    print("=" * 80)
    
    bybit = BybitConnector(mode=BYBIT_API_MODE)
    
    # Busca candles
    klines = bybit.get_klines("BTCUSDT", "5m", limit=30)
    
    if klines:
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        current_price = closes[-1]
        
        # Calcula ATR
        calc = VolatilityCalculator()
        vol_data = calc.get_volatility_data(
            "BTCUSDT", "5m", current_price, highs, lows, closes
        )
        
        if vol_data:
            print(f"\nATR Value: {vol_data.atr_value:.2f}")
            print(f"ATR %: {vol_data.atr_percent:.2f}%")
            print(f"Volatility Regime: {calc.get_volatility_regime(vol_data.atr_percent)}")
            
            # Stop loss dinâmico
            entry = 42500
            stop = calc.calculate_stop_loss(entry, "long", vol_data.atr_value)
            print(f"\nEntry: ${entry:.2f}")
            print(f"Stop (Long): ${stop:.2f} (distância: {entry - stop:.2f})")


async def example_expectancy():
    """Exemplo 4: Cálculo de Expectancy"""
    print("\n" + "=" * 80)
    print("EXEMPLO 4: Expectancy Calculation")
    print("=" * 80)
    
    # Simula dados de trades
    trades_data = [
        {"win": True, "amount": 50},
        {"win": True, "amount": 45},
        {"win": False, "amount": -20},
        {"win": True, "amount": 55},
        {"win": False, "amount": -18},
        {"win": True, "amount": 48},
        {"win": True, "amount": 52},
        {"win": False, "amount": -22},
        {"win": True, "amount": 60},
        {"win": False, "amount": -15},
    ]
    
    wins = sum(t["amount"] for t in trades_data if t["win"])
    losses = sum(abs(t["amount"]) for t in trades_data if not t["win"])
    win_trades = len([t for t in trades_data if t["win"]])
    total_trades = len(trades_data)
    
    win_rate = win_trades / total_trades
    avg_win = wins / win_trades
    avg_loss = losses / (total_trades - win_trades)
    rr_ratio = avg_win / avg_loss
    
    expectancy = (win_rate * rr_ratio) - (1 - win_rate)
    
    print(f"\nWin Rate: {win_rate:.0%}")
    print(f"Avg Win: ${avg_win:.2f}")
    print(f"Avg Loss: ${avg_loss:.2f}")
    print(f"RR Ratio: {rr_ratio:.2f}x")
    print(f"\nExpectancy = W × R - (1-W)")
    print(f"Expectancy = {win_rate:.0%} × {rr_ratio:.2f} - {1-win_rate:.0%}")
    print(f"Expectancy = {expectancy:+.0%}")
    
    if expectancy > 0.05:
        print(f"\n✓ Sistema LUCRATIVO com {expectancy:.0%} expectancy!")
    elif expectancy > 0:
        print(f"\n⚠️ Sistema ligeiramente positivo")
    else:
        print(f"\n❌ Sistema NEGATIVO")


async def main():
    """Menu principal"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║           EXEMPLOS - IaTrade Agents                     ║
    ╚════════════════════════════════════════════════════════╝
    
    Escolha um exemplo:
    1. Market Analysis (detecta setups)
    2. Position Sizing (calcula posição)
    3. Volatility (calcula ATR)
    4. Expectancy (rastreia performance)
    """)
    
    choice = input("Escolha [1-4]: ").strip()
    
    if choice == "1":
        await example_market_analysis()
    elif choice == "2":
        await example_position_sizing()
    elif choice == "3":
        await example_volatility()
    elif choice == "4":
        await example_expectancy()
    else:
        print("Inválido")


if __name__ == "__main__":
    asyncio.run(main())
