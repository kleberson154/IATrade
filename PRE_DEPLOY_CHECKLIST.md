# ✅ CHECKLIST PRÉ-DEPLOY

## 📋 Verificações Locais (Seu PC)

- [ ] Python 3.8+ instalado (`python --version`)
- [ ] Todos os arquivos criados (ver lista abaixo)
- [ ] Diretórios criados: `logs/`, `data/`, `exports/`, `models/`
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] `.env` preenchido com suas credenciais
- [ ] `test_setup.py` passando (todas as checks ✅)
- [ ] `example_integration.py` rodou com sucesso
- [ ] Recebeu notificação teste no Telegram
- [ ] Git inicializado e `.gitignore` em lugar

### Arquivos Verificar:

```
✅ .env                          - Suas credenciais
✅ .env.example                  - Template
✅ .gitignore                    - Protege .env
✅ requirements.txt              - Dependências
✅ dashboard.py                  - Monitor Telegram
✅ start_bot_24h.py              - Gerenciador 24h
✅ test_setup.py                 - Validação
✅ example_integration.py        - Exemplos
✅ utils/telegram_notifier.py    - Notificador
✅ utils/trade_tracker.py        - Rastreador
✅ DEPLOYMENT.md                 - Guia Oracle
✅ GITHUB_GUIDE.md               - Guia GitHub
✅ iatrade.service               - Systemd service
✅ SISTEMA_NOTIFICACOES.md       - Notificações
✅ RESUMO_TELEGRAM.md            - Resumo
✅ README_NOVO.md                - README completo
```

### Credenciais Verificar:

```
.env deve ter:
✅ TELEGRAM_TOKEN=seu_token_aqui
✅ TELEGRAM_CHAT_ID=seu_id_aqui
✅ BYBIT_API_KEY=sua_key_aqui
✅ BYBIT_API_SECRET=seu_secret_aqui
✅ BYBIT_MODE=demo
✅ Outros settings (LOG_FILE, etc)
```

## 🐙 Preparação GitHub

- [ ] Repositório criado no GitHub
- [ ] `.env` NÃO no git (verificar: `git status | grep ".env"`)
- [ ] Todos os arquivos .py em staging
- [ ] Commit message significativa
- [ ] Push para main branch
- [ ] README.md mostra corretamente no GitHub
- [ ] `.env.example` visível para instruções

### Comandos:

```bash
git init
git add .
git status  # Verificar que .env NÃO aparece
git commit -m "Initial commit: IaTrade with Telegram Dashboard"
git branch -M main
git remote add origin https://github.com/seu-usuario/IaTrade.git
git push -u origin main
```

## 🖥️ Preparação Oracle

- [ ] Conta Oracle Always Free criada
- [ ] VM instância criada (Ubuntu 22.04)
- [ ] SSH acesso funcionando
- [ ] Security rules permitindo saída (já está por padrão)

### Comandos para testar SSH:

```bash
ssh ubuntu@seu_ip_oracle
exit
```

## 🚀 Deploy Oracle (Checklist Durante)

- [ ] Repo clonado em `/home/ubuntu/IaTrade`
- [ ] venv criado
- [ ] Dependências instaladas
- [ ] `.env` criado com suas credenciais
- [ ] `test_setup.py` passou ✅
- [ ] `iatrade.service` copiado para `/etc/systemd/system/`
- [ ] `sudo systemctl daemon-reload` executado
- [ ] `sudo systemctl enable iatrade.service` executado
- [ ] `sudo systemctl start iatrade.service` executado
- [ ] `sudo systemctl status iatrade.service` mostra `active (running)`
- [ ] Telegram recebendo notificações

### Comandos Oracle:

```bash
ssh ubuntu@seu_ip_oracle
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env  # Preencher credenciais
python test_setup.py
sudo cp iatrade.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable iatrade.service
sudo systemctl start iatrade.service
sudo systemctl status iatrade.service
sudo journalctl -u iatrade.service -f  # Ver logs
```

## 📱 Teste Telegram

- [ ] Recebeu notificação de test no Telegram
- [ ] Notificação mostra timestamp correto
- [ ] Notificação mostra dados corretos
- [ ] Recebendo cada 2h relatório (aguarde o horário)

### URL Telegram:

- Seu chat: https://t.me/seu_username

## 🔍 Validações Finais

### Local:

```bash
# Rodar tudo
python test_setup.py

# Resultado esperado:
# ✅ Python 3.11.9 OK
# ✅ Todos os arquivos presentes
# ✅ Diretórios criados
# ✅ Dependências instaladas
# ✅ .env configurado
# ✅ Telegram OK
```

### Oracle:

```bash
# SSH na VM
ssh ubuntu@seu_ip

# Verificar serviço
sudo systemctl status iatrade.service

# Ver logs em tempo real
sudo journalctl -u iatrade.service -f

# Saída esperada:
# ✅ active (running)
# ✅ Processando trades
# ✅ Enviando notificações
```

## 🎯 Sucessos Esperados

### ✅ Telegram

- [ ] Notificação de startup
- [ ] Notificação de nova trade
- [ ] Relatório a cada 2h
- [ ] Sem erros nos logs

### ✅ Oracle

- [ ] Serviço running
- [ ] Sem CPU maxed
- [ ] Processos ativos (bot + dashboard)
- [ ] Auto-restart se cair

### ✅ Performance

- [ ] Bot respondendo rápido
- [ ] Notificações chegando em <5s
- [ ] Dashboard não consumindo muita RAM

## 🚨 Problemas Comuns

| Problema             | Solução                                               |
| -------------------- | ----------------------------------------------------- |
| Telegram não recebe  | Verificar TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env   |
| Erro Bybit           | Verificar API_KEY, API_SECRET e BYBIT_MODE            |
| Serviço não inicia   | `sudo systemctl status iatrade.service` para ver erro |
| Processo morreu      | Systemd auto-restart em 60s, verificar `journalctl`   |
| `.env` foi commitado | Remover com `git rm --cached .env`                    |

## 📊 Métricas para Validar

Após 2 horas de operação:

- [ ] Bot fez pelo menos 1 trade
- [ ] Trade apareceu no Telegram
- [ ] Estatísticas calculadas corretamente
- [ ] Relatório de 2h chegou
- [ ] Não há erros nos logs
- [ ] Processo ainda running

## 📝 Documentação Consultar

Se tiver dúvida sobre:

- **Deploy Oracle**: Consulte `DEPLOYMENT.md`
- **GitHub Upload**: Consulte `GITHUB_GUIDE.md`
- **Notificações**: Consulte `SISTEMA_NOTIFICACOES.md`
- **Resumo Geral**: Consulte `RESUMO_TELEGRAM.md`
- **Exemplos**: Consulte `example_integration.py`

## ✨ Bônus: Monitoramento Remoto

Conectar na Oracle e monitorar:

```bash
# SSH da sua máquina
ssh ubuntu@seu_ip_oracle

# Ver status
sudo systemctl status iatrade.service

# Ver últimas linhas do log
sudo journalctl -u iatrade.service -n 50

# Ver logs em tempo real
sudo journalctl -u iatrade.service -f

# Contar trades
wc -l logs/bot_trades.log

# Ver última trade
tail -1 logs/bot_trades.log | python -m json.tool
```

## 🎉 SUCCESS CRITERIA

Sistema está ready quando:

1. ✅ `test_setup.py` passa localmente
2. ✅ GitHub repo criado com todos arquivos
3. ✅ Oracle serviço running 24h
4. ✅ Telegram recebendo notificações
5. ✅ Trades sendo rastreadas
6. ✅ Relatórios de 2h enviados
7. ✅ Sem erros nos logs

**Quando tudo estiver ✅, seu bot está 100% READY! 🚀**

---

## 📞 Quick Support

Cada checklist falhando:

### ❌ test_setup.py falha:

```bash
# Problema: Dependências
python -m pip install --upgrade pip
pip install -r requirements.txt

# Problema: .env não existe
cp .env.example .env
nano .env  # Preencher
```

### ❌ GitHub push falha:

```bash
# Verificar que .env não está em staging
git status | grep ".env"

# Se aparecer, remover
git rm --cached .env
git commit -m "Remove .env from tracking"
```

### ❌ Oracle systemd não funciona:

```bash
# Ver erro completo
sudo systemctl status iatrade.service

# Ver logs
sudo journalctl -u iatrade.service | tail -50

# Reiniciar
sudo systemctl restart iatrade.service
```

---

**Use este checklist antes de declarar ready! ✅**

_Última atualização: Abril 2024_
