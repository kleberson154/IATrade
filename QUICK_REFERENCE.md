# 🚀 QUICK REFERENCE CARD

Imprima ou salve este arquivo para referência rápida!

## 🔧 Comandos Essenciais

### Desenvolvimento Local

```bash
# Setup inicial
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Validar setup
python test_setup.py

# Testar notificações
python example_integration.py

# Rodar bot + dashboard
python start_bot_24h.py

# Rodar separado (debugging)
python main.py            # Terminal 1
python dashboard.py       # Terminal 2
```

### Git & GitHub

```bash
# Primeiro commit
git init
git add .
git commit -m "Initial: IaTrade Telegram Dashboard"
git remote add origin https://github.com/user/IaTrade.git
git branch -M main
git push -u origin main

# Updates
git add .
git commit -m "Your message"
git push
```

### Oracle & Systemd

```bash
# SSH
ssh ubuntu@seu_ip_oracle

# Deploy setup
git clone https://github.com/user/IaTrade.git
cd IaTrade
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env
python test_setup.py

# Systemd
sudo cp iatrade.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable iatrade.service
sudo systemctl start iatrade.service
sudo systemctl status iatrade.service

# Logs em tempo real
sudo journalctl -u iatrade.service -f
```

## 📁 Arquivos Importantes

| Arquivo            | Função           | Quando Usar               |
| ------------------ | ---------------- | ------------------------- |
| `.env`             | Credenciais      | Nunca commit!             |
| `main.py`          | Bot principal    | `python main.py`          |
| `dashboard.py`     | Monitor Telegram | `python dashboard.py`     |
| `start_bot_24h.py` | Tudo junto       | `python start_bot_24h.py` |
| `test_setup.py`    | Validar setup    | Sempre antes de deploy    |
| `requirements.txt` | Dependências     | Após clonar repo          |

## 📱 Notificações Telegram

**Como receber:**

1. Criar bot com @BotFather
   - `/newbot` → Name → Username → Salvar token

2. Obter seu Chat ID
   - `/getuseridbot` → Forward msg → Ver ID
   - Ou: https://api.telegram.org/bot{TOKEN}/getUpdates

3. Adicionar ao `.env`

   ```
   TELEGRAM_TOKEN=seu_token
   TELEGRAM_CHAT_ID=seu_id
   ```

4. Testar
   ```bash
   python test_setup.py
   ```

## 🔑 API Keys Bybit

**Criar em:** https://www.bybit.com/app/user/api-management

1. Criar nova API Key
2. Permissions: Trading (Read), Orders (Read), Position (Read)
3. Restringir IP (sua casa ou server Oracle)
4. Salvar Key + Secret no `.env`

**Modos Bybit:**

- `demo` - Modo demonstração (seguro)
- `testnet` - Testnet (também seguro)
- `real` - Conta real (usar com cuidado!)

**Começar em:** `demo`

## ⏰ Agendamento Telegram

**Automático:**

- ✅ Nova trade → Notificação imediata
- ✅ A cada 2h → Relatório stats
- ✅ Erro → Alerta imediato

**Configurar intervalo:**

```python
# Em .env
DASHBOARD_UPDATE_INTERVAL=7200  # segundos (2h)
```

## 🛡️ Segurança Checklist

- [ ] `.env` tem `.gitignore`
- [ ] Nunca comitou `.env`
- [ ] API Keys restritas por IP
- [ ] Testnet/demo antes de real
- [ ] Senha bot forte
- [ ] Notificações via HTTPS

## 🐛 Debugging Rápido

### Problema: Nada acontece

```bash
ps aux | grep python     # Ver processos
python test_setup.py     # Validar tudo
tail -f logs/dashboard.log  # Ver logs
```

### Problema: Telegram não funciona

```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('TELEGRAM_TOKEN'))
print(os.getenv('TELEGRAM_CHAT_ID'))
"
```

### Problema: Bybit não responde

```bash
python -c "
from connectors.bybit_connector import BybitConnector
c = BybitConnector()
print(c.test_connection())
"
```

## 📊 Estrutura de Dados

### Trade (JSON em logs/bot_trades.log)

```json
{
  "trade_id": "BTCUSDT_20240120_150000",
  "symbol": "BTCUSDT",
  "direction": "long",
  "entry_price": 45000.0,
  "entry_time": "2024-01-20T15:00:00",
  "stop_loss": 44500.0,
  "take_profit": 46000.0,
  "position_size": 0.1,
  "exit_price": 46000.0,
  "exit_time": "2024-01-20T15:30:00",
  "exit_reason": "tp",
  "pnl_usd": 100.0,
  "pnl_percent": 0.22,
  "status": "closed"
}
```

### Estatísticas Calculadas

```python
{
    "total_trades": 100,
    "wins": 18,
    "losses": 82,
    "win_rate": 18.0,
    "total_pnl": 2052.67,
    "avg_win": 114.04,
    "avg_loss": -32.91,
    "rr_ratio": 7.68,
    "max_drawdown": 1234.56,
    "max_win": 450.00,
    "max_loss": -150.00
}
```

## 🎯 Objetivos por Fase

### Fase 1: Local (Hoje)

- [ ] Clonar repo
- [ ] Setup venv + pip
- [ ] Preencher .env
- [ ] Rodar test_setup.py ✅
- [ ] Testar notificações

### Fase 2: GitHub (Hoje)

- [ ] Criar repo no GitHub
- [ ] Git push
- [ ] Verificar no GitHub

### Fase 3: Oracle (Amanhã)

- [ ] Criar VM Ubuntu
- [ ] SSH acesso
- [ ] Clone + setup
- [ ] Systemd service
- [ ] Monitorar logs

### Fase 4: Produção (Semana)

- [ ] Rodar 24h
- [ ] Coletar estatísticas
- [ ] Validar performance
- [ ] Integrar com seu sistema

## 📞 Quick Troubleshooting Matrix

| Sintoma               | Causa Provável       | Fix                               |
| --------------------- | -------------------- | --------------------------------- |
| test_setup.py falha   | Dependência faltando | `pip install -r requirements.txt` |
| Sem notificações      | Token/ChatID errado  | Verificar `.env`                  |
| Bybit connection fail | API Key inválida     | Gerar nova no painel Bybit        |
| Serviço não starts    | Permissões           | `sudo chmod +x /path/to/script`   |
| Logs vagos            | PYTHONUNBUFFERED     | Set em `.env`                     |
| CPU alta              | Benchmark query      | Reduzir frequência                |
| Disk full             | Logs crescendo       | `truncate -s 0 logs/debug.log`    |

## 🔄 Fluxo Típico de Operação

```
HORÁRIO     | EVENTO
06:00 - 18:00 | Bot rodando (seu PC ou Oracle)
18:00       | Bot continua rodando em Oracle (você dorme)
Sempre      | Telegram recebe notificações
A cada 2h   | Relatório de estatísticas
24/7        | Systemd monitora e reinicia se falhar
```

## 📚 Referências Rápidas

**Python / Venv:**

```bash
which python3.11
python -m venv venv
source venv/bin/activate
deactivate
```

**Git:**

```bash
git status
git log --oneline
git diff
git stash
```

**Systemd:**

```bash
sudo systemctl list-units --type service
sudo systemctl restart iatrade
sudo systemctl stop iatrade
sudo journalctl --help
```

**Telegram Bot:**

- Token format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`
- Chat ID format: `1234567890` (números)
- API: `https://api.telegram.org/bot{TOKEN}/sendMessage`

## ✅ Validação Pré-Deploy

Sempre executar:

```bash
# 1. Validar tudo
python test_setup.py

# 2. Testar notificações
python example_integration.py

# 3. Verificar GitHub
git status | grep ".env"  # Não deve aparecer

# 4. Listar arquivos
ls -la

# 5. Pronto!
echo "✅ Tudo pronto para deploy"
```

## 🎓 Aprendizado Importante

> **Nunca comita .env para Git!**

> **Sempre teste em demo antes de real!**

> **Sempre valide com test_setup.py!**

> **Systemd auto-restart salva vidas!**

---

**Salve este arquivo para referência rápida! 💾**

_Print-friendly version ready_
