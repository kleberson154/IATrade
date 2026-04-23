# IaTrade - Robô de Trading Automático com Dashboard Telegram 24h

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Production Ready](https://img.shields.io/badge/status-production%20ready-brightgreen.svg)]()

## 📋 Visão Geral

IaTrade é um **robô de trading automático** que:

- 🤖 Detecta setups de mean reversion + momentum
- 💰 Realiza operações automáticas na Bybit
- 📱 Envia notificações em tempo real via Telegram
- 📊 Gera relatórios de estatísticas a cada 2 horas
- 🔄 Roda 24/7 em servidor (Oracle Always Free, AWS, etc)
- 📈 Histórico completo de trades com análises

## 🎯 Performance

```
Backteste (3.244 trades):
✅ Total P&L: +$2.052,67
✅ Ganhadoras: 610 (18.8%)
✅ Taxa Acerto: 18.8%
✅ Razão Risk/Reward: 7.68x
✅ Risco por trade: 1%
```

## 🚀 Quick Start

### 1. Instalação Local

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env
nano .env  # Adicione suas keys do Bybit e token Telegram
```

### 2. Validar Setup

```bash
python test_setup.py
```

Resultado esperado:

```
✅ Python 3.11.9 OK
✅ Todos os arquivos presentes
✅ Dependências instaladas
✅ .env configurado
✅ Telegram conectado
```

### 3. Testar Notificações

```bash
python example_integration.py
```

### 4. Rodar Bot + Dashboard

```bash
# Opção A: Rodando separadamente (desenvolvimento)
python main.py              # Terminal 1 - Bot principal
python dashboard.py         # Terminal 2 - Dashboard

# Opção B: Rodando tudo junto (produção)
python start_bot_24h.py
```

## 📱 Notificações Telegram

O bot envia automaticamente para seu Telegram:

### 🔔 Notificação de Nova Trade

```
📈 NOVA TRADE

Símbolo: BTCUSDT
Direção: LONG
Entrada: $45000.00
Stop Loss: $44500.00
Take Profit: $46000.00
Tamanho: 0.1
Risco/Recompensa: 1:2.00
Hora: 2024-01-20 15:30:00
```

### 📊 Relatório Periódico (a cada 2h)

```
📊 RELATÓRIO ÚLTIMAS 2 HORAS

Total de Trades: 12
Ganhadoras: 8 ✅
Perdedoras: 4 ❌
Taxa de Acerto: 66.7%
💰 P&L: +$150.00
Lucro Médio: $18.75
Razão R/R: 3.75x
Max Drawdown: $45.00
```

## ⚙️ Configuração

### `.env` - Credenciais (obrigatório criar)

```bash
# Telegram Bot
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_id_aqui

# Bybit
BYBIT_API_KEY=sua_key_aqui
BYBIT_API_SECRET=seu_secret_aqui
BYBIT_MODE=demo  # demo, testnet ou real

# Sistema
SYMBOLS=BTCUSDT,ETHUSDT,LINKUSDT
DASHBOARD_UPDATE_INTERVAL=7200
LOG_FILE=logs/bot_trades.log
```

Ver `.env.example` para template completo.

## 📚 Estrutura do Projeto

```
IaTrade/
├── main.py                 # Bot principal
├── dashboard.py            # Dashboard Telegram
├── start_bot_24h.py        # Gerenciador 24h
│
├── agents/                 # Agentes de IA
│   ├── market_analysis_agent.py
│   ├── risk_management_agent.py
│   └── execution_agent.py
│
├── core/                   # Núcleo de trading
│   ├── backtester.py
│   ├── setup_detector.py
│   ├── position_sizing.py
│   ├── stop_loss_calculator.py
│   └── take_profit_calculator.py
│
├── connectors/             # Integrações
│   ├── bybit_connector.py
│   └── data_provider.py
│
├── utils/                  # Utilidades
│   ├── telegram_notifier.py  # ✨ Notificações
│   └── trade_tracker.py      # ✨ Rastreamento
│
├── logs/                   # Histórico
│   └── bot_trades.log      # JSON lines das trades
│
├── exports/                # Exportações
│   └── trades_export.csv
│
├── DEPLOYMENT.md           # Guia Oracle Always Free
├── GITHUB_GUIDE.md         # Como fazer push
├── SISTEMA_NOTIFICACOES.md # Sistema de notificações
├── requirements.txt        # Dependências
├── .env.example            # Template .env
├── .gitignore              # Protege .env
└── README.md               # Este arquivo
```

## 🔄 Fluxo de Operação

```
┌─────────────────────────────────────────────┐
│        Bot Principal (main.py)              │
├─────────────────────────────────────────────┤
│ 1. Busca dados de mercado (Bybit)          │
│ 2. Detecta setups (Mean Reversion + Mom)   │
│ 3. Calcula risco/recompensa                 │
│ 4. Executa trade                            │
│ 5. Registra em arquivo                      │
└────────────────┬────────────────────────────┘
                 │
                 ├────→ Trade Tracker
                 │      └─→ logs/bot_trades.log
                 │
                 ├────→ Dashboard (dashboard.py)
                 │      ├─→ Detecta nova trade
                 │      ├─→ Envia notificação Telegram
                 │      └─→ A cada 2h: Envia relatório
                 │
                 └────→ Notificador Telegram
                        └─→ Seu celular 📱
```

## 🛠️ Tecnologias Usadas

- **Python 3.8+** - Linguagem
- **Bybit API** - Exchange
- **Telegram Bot API** - Notificações
- **Pandas/NumPy** - Análise de dados
- **Asyncio** - Programação assíncrona
- **FastAPI** - API (opcional)

## 📖 Documentação

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Como rodar 24h na Oracle Always Free
- **[GITHUB_GUIDE.md](GITHUB_GUIDE.md)** - Como fazer push para GitHub
- **[SISTEMA_NOTIFICACOES.md](SISTEMA_NOTIFICACOES.md)** - Sistema de notificações
- **[example_integration.py](example_integration.py)** - Exemplos de código

## 🌐 Deploy na Oracle Always Free (24h)

### Pré-requisitos:

- Conta Oracle Always Free (grátis)
- SSH client

### Instalação (10 minutos):

```bash
# 1. SSH na instância
ssh ubuntu@seu_ip_oracle

# 2. Clonar repo
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade

# 3. Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar .env
nano .env

# 5. Validar
python test_setup.py

# 6. Setup systemd
sudo cp iatrade.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable iatrade.service
sudo systemctl start iatrade.service

# 7. Verificar status
sudo systemctl status iatrade.service
```

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para guia completo.

## 🔐 Segurança

- ✅ `.env` está no `.gitignore` - Credenciais nunca são commitadas
- ✅ Token Telegram protegido
- ✅ API Keys Bybit nunca expostas
- ✅ HTTPS para todas as conexões
- ✅ Sem logs de credenciais

## 📊 Análises & Exportação

```bash
# Exportar histórico de trades
python -c "
from utils.trade_tracker import TradeTracker
tracker = TradeTracker()
tracker.export_to_csv('meu_historico.csv')
"

# Ver estatísticas
python -c "
from utils.trade_tracker import TradeTracker
tracker = TradeTracker()
trades = tracker.get_all_trades()
stats = tracker.calculate_stats(trades)
print(stats)
"
```

## 🐛 Troubleshooting

### Telegram não recebendo notificações

```bash
python test_setup.py  # Verifica token e chat_id
```

### Erro ao conectar na Bybit

```bash
# Verificar API key/secret no .env
# Verificar se está em modo demo/testnet correto
python -c "from connectors.bybit_connector import BybitConnector; c = BybitConnector(); print(c.test_connection())"
```

### Processos não reiniciando

```bash
# Ver logs
sudo journalctl -u iatrade.service -f

# Reiniciar manualmente
sudo systemctl restart iatrade.service
```

## 🤝 Contribuindo

1. Fork o repositório
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes

## ⚠️ Disclaimer

- Este é software educacional
- Sempre teste em modo `demo` antes de `real`
- Trading é arriscado - comece pequeno
- Nunca use dinheiro que não possa perder
- O desempenho passado não garante futuro

## 🙋 Suporte

- 📖 Veja a documentação em `DEPLOYMENT.md` e `GITHUB_GUIDE.md`
- 🔍 Consulte `example_integration.py` para exemplos
- ✅ Execute `test_setup.py` para validar setup
- 📋 Leia o [RESUMO_TELEGRAM.md](RESUMO_TELEGRAM.md)

## 📈 Roadmap

- [ ] Dashboard web com FastAPI
- [ ] Banco de dados para histórico
- [ ] Gráficos em tempo real
- [ ] Mais exchanges (Binance, Kraken)
- [ ] Machine Learning para sinais
- [ ] Trading pairs automático

---

**Desenvolvido com ❤️ para automação de trading**

_Status: ✅ Production Ready_  
_Última atualização: Abril de 2024_
