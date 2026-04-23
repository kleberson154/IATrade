# INTEGRATION CHECKLIST - IaTrade

## ✅ Fase 1: Setup Inicial (COMPLETO)

- [x] Estrutura de diretórios criada
- [x] 4 Agentes de IA implementados
  - [x] Market Analysis Agent
  - [x] Risk Management Agent
  - [x] Execution Agent
  - [x] Performance Monitor Agent
- [x] Core components
  - [x] Volatility Calculator (ATR)
  - [x] Position Sizer
  - [x] Setup Detector
- [x] Bybit Connector (com simulação)
- [x] Trade Journal (CSV + JSON)
- [x] Main Orchestrator

## 🔧 Fase 2: Testes Locais (PRÓXIMO)

- [ ] **1. Validar Imports**
  ```bash
  python -c "from main import TradingBot; print('✓ OK')"
  ```
- [ ] **2. Teste Setup (Check Configuration)**
  ```bash
  python quickstart.py
  ```
- [ ] **3. Simulação 10 Trades**
  ```bash
  python main.py
  # Escolha: 1 (simulação)
  ```

  - Verifica detecta setups
  - Calcula position sizing
  - Rastreia expectancy
- [ ] **4. Live DRY_RUN (5 minutos)**
  ```bash
  python main.py
  # Escolha: 2 (live)
  ```

  - Simula ordens em tempo real
  - Verifica conectividade

## 🔐 Fase 3: Credenciais Bybit (APÓS TESTES)

### 3.1 Obter Credenciais

- [ ] Criar conta demo em https://www.bybit.com (demo account)
- [ ] Account > API Management
- [ ] Create Key (Demo)
  - Label: "IaTrade"
  - Permissions:
    - [x] Read (posições, dados)
    - [x] Write (ordens)
    - [x] Account (wallet)
  - Copy:
    - API Key
    - API Secret

### 3.2 Configurar Credenciais

- [ ] Editar `config/settings.py`:
  ```python
  BYBIT_API_KEY = "sua_chave_demo_aqui"
  BYBIT_API_SECRET = "seu_secret_demo_aqui"
  BYBIT_API_MODE = "demo"  # IMPORTANTE: demo, não testnet
  ```

### 3.3 Testar Conexão

```bash
python -c "
from connectors.bybit_connector import BybitConnector
bybit = BybitConnector(mode='demo')
info = bybit.get_account_info()
print(f'✓ Account Balance: {info.get(\"available_balance\")}')
"
```

## 🚀 Fase 4: Validação em Demo (1-2 semanas)

- [ ] **Semana 1: Backtesting**
  - [ ] Rodar 50+ ciclos de simulação
  - [ ] Verificar Expectancy > 0.05
  - [ ] Ajustar parâmetros se necessário
- [ ] **Semana 2: Paper Trading (DRY_RUN)**
  - [ ] Deixar rodando 2-3 dias
  - [ ] Monitorar sinais gerados
  - [ ] Verificar win rate vs expectancy
  - [ ] Confirmar não há erros de API

- [ ] **Testes de Stress**
  - [ ] [ ] Mercado muito volátil (ATR > 2%)
  - [ ] [ ] Mercado congelado (ATR < 0.3%)
  - [ ] [ ] Conexão instável (reconnect)
  - [ ] [ ] Ordens atrasadas (timeout)

## 💰 Fase 5: Primeira Execução Real em Demo

- [ ] Usar conta demo da Bybit com "dinheiro real" (saldo demo)
- [ ] Setar `DRY_RUN = False`
- [ ] Rodar com MAX_TRADES_PER_DAY = 5 (conservador)
- [ ] Monitorar CADA trade manualmente
- [ ] Registrar todas as issues
- [ ] **NÃO** colocar em modo automático puro

### Sinais de Alerta (PARAR IMEDIATAMENTE)

- ❌ Expectancy cai abaixo de 0
- ❌ Win rate < 30% por mais de 20 trades
- ❌ Erros recorrentes de API
- ❌ Position sizing errado (muito grande/pequeno)
- ❌ Stops não sendo colocados

## 🎓 Fase 6: Refinamento (Iterativo)

### Performance Review a cada 20 trades:

- [ ] Expectancy ainda positiva?
- [ ] Setups ainda válidos?
- [ ] Algum setup vencendo mais que outros?
- [ ] Ajustar confiança mínima?
- [ ] Ajustar ATR multiplier?

### Exemplo: Se Mean Reversion vence muito

```python
# config/settings.py
SETUP_CONFIGS[SetupType.MEAN_REVERSION]["expected_rr"] = 1.8  # antes: 1.5
```

## 📊 Fase 7: Scale-Up Gradual (Depois de validado)

- [ ] Aumentar MAX_TRADES_PER_DAY: 5 → 10
- [ ] Aumentar RISK_PER_TRADE_PERCENT: 0.5% → 1%
- [ ] Adicionar mais símbolos (depois, não agora)
- [ ] Aumentar timeframes monitorados

## 🔒 Fase 8: Produção (Se 3+ meses positivo)

- [ ] Setup VPS Linux
- [ ] Python 3.9+ + dependencies
- [ ] Cron job para auto-start
- [ ] Telegram alerts (opcional)
- [ ] Dashboard web (opcional)
- [ ] DEPOIS usar conta real (com micro volume)

---

## 📋 Checklist de Segurança Permanente

ANTES de cada execução:

- [ ] `DRY_RUN` correto?
  - Demo: DRY_RUN=True em primeiro
  - Real: DRY_RUN=False APENAS após validação
- [ ] `BYBIT_API_MODE` correto?
  - "demo" para testes
  - "testnet" para testnet (menos recomendado)
  - "real" para conta real
- [ ] `MAX_TRADES_PER_DAY` está razoável?
  - Início: 5 trades/dia
  - Depois: 10 trades/dia máximo
- [ ] `RISK_PER_TRADE_PERCENT` entre 0.5-2%?
- [ ] Credenciais têm permissões corretas?
  - [x] Read
  - [x] Write (não precisa Transfer!)
  - [x] Account

- [ ] Logs estão sendo salvos?
  - Verificar `logs/trading_bot.log`
  - Verificar `logs/trades_*.csv`

---

## 🚨 Troubleshooting Common Issues

### Erro: "Bybit connector não configurado"

```
Solução: Adicionar API_KEY e API_SECRET em settings.py
         Ou rodar em modo simulado (DRY_RUN=True)
```

### Erro: "Position size inválido"

```
Solução:
  - Aumentar ACCOUNT_SIZE_USDT
  - Reduzir RISK_PER_TRADE_PERCENT
  - Aumentar stop distance (stop mais longe)
```

### Erro: "RR muito baixo"

```
Solução:
  - Aumentar TP (pegar maior lucro)
  - Reduzir stop distance
  - Aceitar sinal mais confiante
```

### Nenhum setup detectado

```
Solução:
  - Esperar mais (mercado sem movimento)
  - Reduzir thresholds de confiança mínima
  - Verificar dados de klines (get_klines())
  - Verificar ATR está calculando
```

### Ordens falhando

```
Solução:
  - Verificar credenciais Bybit
  - Verificar saldo em demo account
  - Verificar modo (demo vs testnet vs real)
  - Verificar limits de ordem
  - Aumentar ORDER_TIMEOUT_SECONDS
```

---

## 📞 Contatos de Suporte

- **Bybit Demo**: https://demo.bybit.com
- **Bybit API Docs**: https://bybit-exchange.github.io/docs/
- **Bybit Forum**: https://t.me/BYBITofficial
- **Artigo Referência**: "Complete Guide to Profit from 5-15 Minute Markets"

---

## 🎯 Próximas Ações Imediatas

### HOJE:

1. ✅ Validar que código compila
2. ✅ Rodar simulação 10 trades
3. ✅ Verificar logs estão sendo salvos

### ESTA SEMANA:

4. ⏳ Obter credenciais Bybit Demo
5. ⏳ Configurar em settings.py
6. ⏳ Deixar rodando DRY_RUN por 1 dia
7. ⏳ Validar 20+ trades

### PRÓXIMAS 2 SEMANAS:

8. ⏳ Rodar 50+ trades em simulação
9. ⏳ Analisar expectancy real
10. ⏳ Ajustar confiança de setups se necessário

---

## 📈 KPIs de Sucesso

| Métrica                | Alvo   | Status |
| ---------------------- | ------ | ------ |
| Expectancy             | > +5%  | ⏳     |
| Win Rate               | 45-60% | ⏳     |
| RR Ratio               | > 1.5x | ⏳     |
| Max Consecutive Losses | ≤ 3    | ⏳     |
| Profit Factor          | > 1.5  | ⏳     |

---

**Lembre-se: A consistência vence a inteligência. O sistema importa mais do que o trader.**
