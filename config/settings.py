"""
Configurações Centralizadas - IaTrade Bot
=========================================
Todas as settings do bot em um único lugar
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONTA E RISCO
# ============================================================================
ACCOUNT_SIZE_USDT = int(os.getenv("ACCOUNT_SIZE_USDT", "100"))  # Tamanho da conta em USDT (demo)
RISK_PER_TRADE_PERCENT = 1.0  # Risco por trade em % da conta (1%)
MIN_RR_RATIO = 1.5  # Razão mínima Risk/Reward (rejeita abaixo disso)
MAX_TRADES_PER_DAY = 10  # Limite de trades por dia (disciplina)

# ============================================================================
# BYBIT API
# ============================================================================
BYBIT_API_MODE = os.getenv("BYBIT_API_MODE", os.getenv("BYBIT_MODE", "demo"))  # "testnet" | "demo" | "real"
BYBIT_TESTNET_URL = "https://api-testnet.bybit.com"
BYBIT_DEMO_URL = "https://api-demo.bybit.com"
BYBIT_REAL_URL = "https://api.bybit.com"

# Credenciais (deixar vazia para DEMO/TESTNET)
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET", "")

# ============================================================================
# BOT BEHAVIOR
# ============================================================================
DRY_RUN = os.getenv("DRY_RUN", "False")  # True para simulação, False para execução real
SYMBOL = os.getenv("SYMBOL", "BTCUSDT")  # Ativo a tradear
TIMEFRAME = os.getenv("TIMEFRAME", "5")  # Em minutos (5m candles)
TIMEFRAMES_FOR_ANALYSIS = ["5", "15", "1h"]  # Multi-timeframe

# ============================================================================
# SETUP DETECTION
# ============================================================================
# Mean Reversion - quando preço está extremamente baixo (oversold)
MEAN_REVERSION_RSI_THRESHOLD = 30  # RSI < 30 = oversold
MEAN_REVERSION_RANGE_PERCENT = 0.2  # Dentro de 20% do recent_low

# Momentum - quando preço está acelerado para cima
MOMENTUM_RSI_THRESHOLD = 70  # RSI > 70 = overbought/strong
MOMENTUM_MA_SEPARATION = 0.02  # 2% separação entre MAs

# Breakout - quando preço quebra resistência/suporte
BREAKOUT_VOLUME_MULTIPLIER = 1.5  # Volume deve ser 1.5x a média
BREAKOUT_CONFIRMATION_CANDLES = 2  # Confirmar em N velas

# ============================================================================
# VOLATILITY (ATR)
# ============================================================================
ATR_PERIOD = 14  # Período para cálculo de ATR (14 é padrão)
ATR_MULTIPLIER = 2.0  # Multiplicador de ATR para Stop Loss (2x ATR)
ATR_HIGH_VOLATILITY_THRESHOLD = 3.0  # ATR% acima disso = alta volatilidade
ATR_LOW_VOLATILITY_THRESHOLD = 1.0  # ATR% abaixo disso = baixa volatilidade

# ============================================================================
# RISK MANAGEMENT
# ============================================================================
# Proteção de Capital
VOLATILITY_MULTIPLIER = 1.0  # Ajuste de stop por volatilidade
DISALLOW_SIZE_INCREASE_AFTER_N_LOSSES = 1  # Nunca aumentar size após N losses
STOP_DISTANCE_PERCENT = 0.15  # Stop a 15% de distância
STOP_AFTER_2_LOSSES = True  # Para de tradear após 2 losses seguidos

# Take Profits - Distribuição de saída
TP1_PERCENT_GAIN = 0.5  # 1º TP: ~0.5% de lucro (vender 50%)
TP2_PERCENT_GAIN = 1.0  # 2º TP: ~1% de lucro (vender 30%)
TP3_PERCENT_GAIN = 1.5  # 3º TP: ~1.5% de lucro (vender 20%)

TP1_VOLUME_PERCENT = 0.50  # Vender 50% na TP1
TP2_VOLUME_PERCENT = 0.30  # Vender 30% na TP2
TP3_VOLUME_PERCENT = 0.20  # Vender 20% na TP3

# ============================================================================
# EXECUTION
# ============================================================================
USE_MARKET_ORDERS = False  # True = market orders, False = limit orders
ORDER_TIMEOUT_SECONDS = 60  # Timeout para execução de ordem

# ============================================================================
# PERFORMANCE TRACKING
# ============================================================================
TRACK_EXPECTANCY = True  # Acompanhar expectativa de ganho
MIN_ACCEPTABLE_EXPECTANCY = 0.05  # Mínimo 5% expectancy aceitável
REVIEW_PERIOD_TRADES = 20  # Revisar a cada N trades
LOG_LEVEL = "INFO"  # DEBUG | INFO | WARNING | ERROR
SAVE_TRADES_TO_CSV = True  # Salvar histórico em CSV

# ============================================================================
# BACKTESTING
# ============================================================================
BACKTEST_START_DATE = "2024-01-01"  # Data início do backtest
BACKTEST_END_DATE = "2025-12-31"  # Data fim do backtest
BACKTEST_NUM_CANDLES = 5000  # Quantas velas usar na simulação

# ============================================================================
# DADOS SIMULADOS
# ============================================================================
# Para simulação, gera dados ficcionais de BTC
SIMULATION_BTC_STARTING_PRICE = 42500  # Preço inicial do BTC
SIMULATION_VOLATILITY = 0.02  # 2% volatilidade por candle
SIMULATION_TREND_PROBABILITY = 0.55  # 55% chance de continuar trend

print("[OK] Settings carregadas com sucesso!")
print(f"     Mode: {BYBIT_API_MODE} | DRY_RUN: {DRY_RUN} | Account: ${ACCOUNT_SIZE_USDT}")
