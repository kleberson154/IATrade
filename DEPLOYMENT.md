# 🤖 IaTrade - Bot de Trading com Notificações Telegram

Sistema completo de trading automático com notificações em tempo real via Telegram, preparado para rodar 24h em Oracle Free Tier.

## 📋 Características

- ✅ **Backteste avançado**: +$2,052.67 de lucro em 90 dias (18.8% win rate)
- 📊 **Dashboard Telegram**: Relatórios automáticos a cada 2 horas
- 🔔 **Notificações de Trades**: Alerta de cada nova trade aberta
- 📈 **Análise Técnica**: Mean Reversion, Momentum e Fibonacci
- 🔐 **Seguro**: Credenciais em `.env` (nunca commitar)
- 🚀 **24h Ready**: Script para rodar continuamente na Oracle

## 🚀 Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade
```

### 2. Criar Ambiente Virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Credenciais

Criar arquivo `.env` na raiz do projeto:

```env
# Telegram Config
TELEGRAM_TOKEN=seu_token_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui

# Bybit API
BYBIT_API_KEY=sua_chave_aqui
BYBIT_API_SECRET=seu_secret_aqui

# Modo de operação: demo | testnet | real
BYBIT_MODE=demo

# Símbolos a tradear
SYMBOLS=BTCUSDT,ETHUSDT,LINKUSDT

# Dashboard
DASHBOARD_UPDATE_INTERVAL=7200
LOG_FILE=logs/bot_trades.log
```

⚠️ **IMPORTANTE**: Nunca commitar o arquivo `.env`. Já está no `.gitignore`.

## 📝 Uso

### Rodar Backteste

```bash
python scripts/run_backtest_simple.py
```

### Testar Notificações Telegram

```bash
python -m utils.telegram_notifier
```

### Rodar Bot em Modo Demo (Local)

```bash
python main.py
```

### Rodar Bot 24h (com Dashboard)

```bash
python start_bot_24h.py
```

## 🎯 Arquitetura do Sistema

```
IaTrade/
├── agents/              # Agentes de IA (Market, Risk, Execution)
├── connectors/          # Conexões (Bybit, Data Provider)
├── core/               # Núcleo (Backtester, Setup Detector, Fibonacci)
├── models/             # Modelos de dados
├── utils/
│   ├── telegram_notifier.py  # ✨ Notificações Telegram
│   └── trade_tracker.py      # ✨ Rastreamento de trades
├── scripts/            # Scripts úteis
├── dashboard.py        # ✨ Dashboard Telegram 24h
├── start_bot_24h.py    # ✨ Script de inicialização 24h
├── .env               # ⚠️ Credenciais (NÃO COMMITAR)
├── .gitignore         # Arquivos a ignorar no Git
├── requirements.txt   # Dependências Python
└── main.py           # Bot principal
```

## 🏃 Deploy em Oracle Always Free

### 1. Criar Instância

- VM.Standard.A1.Flex (Ampere ARM)
- 4 vCPUs / 24 GB RAM
- 200 GB Storage
- Ubuntu 22.04

### 2. Conectar via SSH

```bash
ssh ubuntu@seu_ip_oracle
```

### 3. Setup Inicial

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python e pip
sudo apt install -y python3.11 python3.11-venv python3.11-dev git

# Clonar repositório
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade

# Criar ambiente virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Criar Arquivo .env

```bash
nano .env
```

Colar as credenciais (Telegram, Bybit, etc) e salvar (Ctrl+X, Y, Enter)

### 5. Testar Conexões

```bash
# Testar Telegram
python -m utils.telegram_notifier

# Testar Bybit (se em BYBIT_MODE=demo)
python main.py
```

### 6. Criar Systemd Service (Rodar Automaticamente)

```bash
sudo nano /etc/systemd/system/iatrade.service
```

Colar:

```ini
[Unit]
Description=IaTrade Bot - Trading Automático 24h
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/IaTrade
Environment="PATH=/home/ubuntu/IaTrade/venv/bin"
ExecStart=/home/ubuntu/IaTrade/venv/bin/python start_bot_24h.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Salvar e habilitar:

```bash
# Habilitar serviço
sudo systemctl enable iatrade.service

# Iniciar serviço
sudo systemctl start iatrade.service

# Ver status
sudo systemctl status iatrade.service

# Ver logs
sudo journalctl -u iatrade.service -f
```

### 7. Verificar Logs

```bash
tail -f logs/bot_manager.log
tail -f logs/dashboard.log
tail -f logs/bot_trades.log
```

### 8. Reiniciar/Parar

```bash
sudo systemctl restart iatrade.service
sudo systemctl stop iatrade.service
```

## 📊 Recebendo Notificações no Telegram

Você receberá:

1. ✅ **Mensagem de Startup** - Quando o bot iniciar
2. 🔔 **Notificação de Trade** - Cada vez que uma nova trade for aberta
3. 📈 **Relatório a cada 2 horas** - Estatísticas do período

Exemplo de notificação:

```
📊 RELATÓRIO DE ESTATÍSTICAS

Período: Últimas 2h
Total de Trades: 12
Ganhadoras: 8 ✅
Perdedoras: 4 ❌
Taxa de Acerto: 66.7%

💰 P&L TOTAL: +$150.00
Lucro Médio: $18.75
Perda Média: -$5.00
Razão R/R: 3.75x
Max Drawdown: $45.00
```

## 🔧 Integração com Bot Atual

O sistema de notificações funciona com o seu bot atual. Você precisa integrar:

```python
from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier

# Em cada trade aberta:
tracker = TradeTracker()
trade = Trade(...)
tracker.add_trade(trade)

# Em cada trade fechada:
tracker.update_trade(trade_id, status="closed", ...)

# Dashboard envia notificações automaticamente
```

## 📦 GitHub Ready

Este repositório está pronto para GitHub com:

✅ `.env` e credenciais no `.gitignore`  
✅ Apenas arquivos necessários  
✅ `requirements.txt` com todas as dependências  
✅ README completo  
✅ Estrutura limpa

Para fazer upload:

```bash
git add .
git commit -m "Initial commit: IaTrade com Dashboard Telegram"
git push origin main
```

## 🤝 Suporte

Para problemas ou dúvidas:

1. Verificar logs: `tail -f logs/*.log`
2. Testar conexão Telegram: `python -m utils.telegram_notifier`
3. Verificar `.env`: Certificar que todas as credenciais estão corretas

## 📄 Licença

MIT License - Veja LICENSE.md

---

**Desenvolvido com ❤️ para trading automático 24h**
