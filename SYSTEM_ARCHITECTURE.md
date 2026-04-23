# SYSTEM ARCHITECTURE - IaTrade

## 🏗️ Arquitetura em Camadas

```
┌─────────────────────────────────────────────────────┐
│                    MAIN ORCHESTRATOR                │
│  (TradingBot - Coordena todos os agentes)           │
└────────────────┬────────────────────────────────────┘
                 │
     ┌───────────┼───────────┬───────────┐
     │           │           │           │
     ▼           ▼           ▼           ▼
   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
   │Market│  │ Risk │  │Exec. │  │Perf. │
   │Agent │  │Agent │  │Agent │  │Agent │
   └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
      │         │         │         │
      └─────────┴─────────┴─────────┘
              │
              ▼
    ┌──────────────────────┐
    │   CORE COMPONENTS    │
    ├──────────────────────┤
    │ • Volatility (ATR)   │
    │ • Position Sizing    │
    │ • Setup Detector     │
    └──────────────────────┘
              │
              ▼
    ┌──────────────────────┐
    │    CONNECTORS        │
    ├──────────────────────┤
    │ • Bybit API (Demo)   │
    │ • Trade Journal      │
    └──────────────────────┘
```

---

## 🔄 Fluxo de Execução

### 1️⃣ **Market Analysis Phase**

```
Bybit API
   │ ← get_klines() [closes, highs, lows, volumes]
   │ ← get_latest_price()
   ▼
Market Analysis Agent
   │
   ├─ Setup Detector
   │  ├─ detect_momentum()    → SetupSignal
   │  ├─ detect_mean_reversion() → SetupSignal
   │  └─ detect_breakout()    → SetupSignal
   │
   ├─ Volatility Calculator
   │  └─ calculate_atr()      → VolatilityData
   │
   └─ Multi-Timeframe Validator
      └─ validate_signal_across_timeframes()

   Output: Best SetupSignal com confiança
```

### 2️⃣ **Risk Management Phase**

```
SetupSignal + VolatilityData
   ▼
Risk Management Agent
   │
   ├─ Position Sizer
   │  ├─ calculate_risk_amount()
   │  ├─ calculate_position_size()
   │  ├─ calculate_take_profits()
   │  └─ validate_rr_ratio()
   │
   └─ Risk Validator
      ├─ Validate RR >= 1.5x
      ├─ Validate Risk <= 1% account
      ├─ Validate Position > 0
      └─ Validate Sizing Discipline

   Output: Complete Trade object
           (entry, stop, TP1/2/3, size, risk/reward)
```

### 3️⃣ **Execution Phase**

```
Validated Trade
   ▼
Execution Agent
   │
   ├─ PHASE 1: Place Entry Order (MARKET)
   │  └─ order_id = place_order()
   │
   ├─ PHASE 2: Set Stop Loss
   │  └─ set_stop_loss(order_id, stop_price)
   │
   └─ PHASE 3: Set Take Profits
      ├─ set_take_profits() - TP1 (50% close)
      ├─ set_take_profits() - TP2 (30% close)
      └─ set_take_profits() - TP3 (20% close)

   Output: Trade OPEN + Monitored
           (Trade ID, Order ID, Open Price/Time)
```

### 4️⃣ **Monitoring & Performance Phase**

```
Open Trade ← Monitor Price
   │        ← Monitor SL/TPs
   │
   ▼ (Trade Closes)
Closed Trade
   │
   ▼
Performance Monitor Agent
   │
   ├─ Calculate PnL
   ├─ Calculate Expectancy: E = W×R - (1-W)
   ├─ Update Win Rate
   ├─ Update Avg Win/Loss
   ├─ Track RR Ratio
   │
   └─ Detect Regime Changes
      ├─ Check if expectancy declining
      ├─ Alert if E < minimum
      └─ Recommend system review

   Output: PerformanceStats
           (Win Rate, Expectancy, RR, etc)

Trade Journal
   └─ Save to CSV/JSON for analysis
```

---

## 📊 Estrutura de Dados

### Trade Object

```python
Trade {
  id: "abc123d4"
  symbol: "BTCUSDT"
  direction: "long"                    # TradeDirection enum
  setup_type: "momentum"               # momentum, mean_reversion, breakout

  entry_price: 42500.00
  entry_size: 0.0234                   # BTC
  entry_time: 2024-04-20 14:30:00

  stop_loss: 41800.00
  tp1: 43500.00                        # 50% posição
  tp2: 44300.00                        # 30% posição
  tp3: 45100.00                        # 20% posição

  status: "open"                       # pending, open, closed, cancelled
  close_price: 43500.00                # TP1 hit
  close_time: 2024-04-20 14:35:00

  pnl_usdt: +39.49
  pnl_percent: +3.95%
  rr_ratio: 1.50
  risk_amount: 10.00
  reward_amount: 39.49

  exit_reason: "tp1"                   # tp1, tp2, tp3, sl, manual
}
```

### SetupSignal Object

```python
SetupSignal {
  setup_type: "momentum"               # 3 tipos
  direction: "long"
  confidence: 0.72                     # 0.0-1.0

  entry_price: 42500.00
  stop_price: 41800.00

  reason: "Quebra de resistência com 4 candles consecutivos UP"
}
```

### VolatilityData Object

```python
VolatilityData {
  atr_value: 385.50                    # Valor absoluto ATR
  atr_percent: 0.905%                  # ATR como % do preço
  current_price: 42500.00

  high_volatility: false               # ATR > 1.5%?
  low_volatility: false                # ATR < 0.5%?
  regime: "NORMAL"                     # HIGH, NORMAL, LOW
}
```

### PerformanceStats Object

```python
PerformanceStats {
  total_trades: 42
  winning_trades: 25
  losing_trades: 17

  win_rate: 0.595                      # 59.5% (W em E = W×R - (1-W))
  avg_win: 35.50
  avg_loss: 18.75
  rr_ratio: 1.89                       # R em E = W×R - (1-W)

  expectancy: 0.512                    # +51.2% (EXCELENTE!)
  expectancy_percent: 51.2%

  total_pnl: 750.25
  gross_profit: 887.50
  gross_loss: -137.25

  profit_factor: 6.47                  # Gross Profit / |Gross Loss|
  max_consecutive_losses: 2
}
```

---

## 🎯 Regras Implementadas (do Artigo)

### 1. **Expectancy = W × R - (1-W)**

- **W**: Win Rate (% de trades vencedoras)
- **R**: Ratio = Avg Win / Avg Loss
- **Interpretação**:
  - E > 0 = Lucrativo ao longo do tempo
  - E > 0.05 = +5% mínimo esperado (bom)
  - E > 0.20 = +20% esperado (muito bom)

### 2. **Position Sizing = (Account × Risk%) / Stop Distance**

- **Account**: $1000 (configurável)
- **Risk%**: 1% por trade (configurável 0.5-2%)
- **Stop Distance**: Preço do stop loss até entry

Exemplo:

```
Position Size = ($1000 × 0.01) / ($42500 - $41800)
Position Size = $10 / $700
Position Size = 0.0143 BTC
```

### 3. **Volatilidade Adaptativa (ATR)**

```
Stop = Entry ± k × ATR

k = 2.0 (multiplicador padrão)
ATR = Average True Range (14 períodos)

Alta volatilidade (ATR > 1.5%):
  → Reduz position size em 25%
  → Mantém risco constante em USD

Baixa volatilidade (ATR < 0.5%):
  → Aumenta position size em 25%
  → Mantém risco constante em USD
```

### 4. **RR Mínimo = 1.5x**

- Trade rejeitada se RR < 1.5
- RR = (TP - Entry) / (Entry - Stop)

### 5. **3 Tipos de Setups**

| Setup          | Win Rate | RR   | Expectancy |
| -------------- | -------- | ---- | ---------- |
| Momentum       | 45%      | 2.0x | +0.35      |
| Mean Reversion | 55%      | 1.5x | +0.275     |
| Breakout       | 50%      | 2.5x | +0.50      |

### 6. **Disciplina**

- ❌ NUNCA aumentar size após loss
- ✋ Máximo 10 trades/dia
- ⏸️ Pausa após 2 perdas
- 🔒 Nunca desviar do sistema

---

## 🔌 Configuração & Deployment

### Development Setup

```bash
# 1. Clone
git clone [seu-repo]
cd IaTrade

# 2. Environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Config
# Editar config/settings.py com credenciais

# 5. Test
python quickstart.py
```

### Production Deployment (VPS)

```
VPS (Linux/Ubuntu)
  │
  ├─ Python 3.9+
  ├─ requirements.txt instalados
  ├─ config/settings.py com credenciais
  └─ Systemd service para auto-start
```

---

## 📈 Monitoramento & Alertas

### KPIs Rastreados

1. **Expectancy** (métrica-chave)
   - Alert: E < 0.05 (abaixo de mínimo aceitável)
   - Alert: E < 0 (sistema perdendo)

2. **Win Rate**
   - Normal: 40-60%
   - Alert: < 35% (muito baixa)

3. **RR Ratio**
   - Mínimo: 1.5x
   - Bom: > 1.8x
   - Alert: < 1.5x

4. **Regime Changes**
   - Detecta queda de 10% em expectancy
   - Recomenda revisão do sistema

### Logs & Outputs

```
logs/
├── trading_bot.log          # Eventos do bot
├── trades_20240420_*.csv    # Histórico em tabela
└── trades_20240420_*.json   # Histórico estruturado
```

---

## 🛡️ Safety Mechanisms

1. **Position Size Validation**
   - Risk não excede 1% da conta
   - Position size > 0

2. **RR Validation**
   - RR >= 1.5x obrigatório
   - Trade rejeitada caso contrário

3. **Discipline Enforcement**
   - Histórico de sizing
   - Rejeita aumentos após loss
   - Max 10 trades/dia

4. **Error Handling**
   - Try/except em todas operações críticas
   - Logs detalhados
   - Graceful shutdown

---

## 🎓 Processo de Aprendizado

1. **Backtest** (50+ trades em simulação)
   → Entender expectancy do sistema

2. **Paper Trade** (DRY_RUN=True)
   → Validar sinais em tempo real

3. **Demo** (Bybit Demo com REAL money)
   → Testar execução com credenciais reais

4. **Live** (Com muito cuidado)
   → Deploy final após validação

---

## ⚠️ Limitações & Conhecidas

1. Sinais em 5-15m (não para 1h+)
2. Apenas BTC por enquanto
3. Requer conexão com internet
4. Latência pode afetar execução
5. Slippage não incluído em simulação

---

## 🚀 Roadmap

- ✅ Core architecture
- ✅ 4 Agents implemented
- ✅ Article rules applied
- ⏳ Bybit integration testing
- ⏳ Multi-symbol support
- ⏳ Advanced indicators (Volume, MACD)
- ⏳ Telegram alerts
- ⏳ Web dashboard

---

**Desenvolvido com foco em Expectancy e Disciplina.**
