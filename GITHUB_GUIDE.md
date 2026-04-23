# 📄 GitHub Upload Guide

## 📦 Arquivos para Upload

Este diretório está pronto para fazer upload no GitHub. Aqui está o que você deve fazer:

### ✅ Arquivos que DEVEM ir para GitHub:

- ✅ Código-fonte Python (`.py`)
- ✅ README.md e DEPLOYMENT.md
- ✅ requirements.txt
- ✅ .gitignore (protege .env)
- ✅ .env.example (template)
- ✅ Diretórios: agents/, core/, connectors/, models/, utils/, scripts/

### ❌ Arquivos que NÃO devem ir:

- ❌ `.env` (credenciais - já no .gitignore)
- ❌ `logs/` (arquivos de log)
- ❌ `data/` (arquivos de dados)
- ❌ `__pycache__/` (cache Python)
- ❌ `venv/` (ambiente virtual)

## 🚀 Passos para Upload

### 1. Criar Repositório no GitHub

```bash
# Ir em https://github.com/new
# Criar repositório chamado "IaTrade"
# Não inicializar com README (já temos)
```

### 2. Adicionar Remote e Fazer Push

```bash
cd IaTrade

# Verificar status
git status

# Ver o que será adicionado
git add --dry-run -A

# Adicionar todos os arquivos
git add .

# Commit
git commit -m "Initial commit: Trading Bot com Dashboard Telegram 24h"

# Adicionar remote
git remote add origin https://github.com/seu-usuario/IaTrade.git

# Push para main
git branch -M main
git push -u origin main
```

### 3. Verificar GitHub

```bash
# Ver logs
git log

# Ver remote
git remote -v
```

## 🔐 Segurança

- ✅ `.env` está no `.gitignore` - suas credenciais são seguras
- ✅ `.env.example` fornece um template para quem clonar
- ✅ Nenhuma senha ou chave API no código

## 📋 Checklist Antes de Fazer Push

- ✅ Remover `venv/` local (será .gitignored)
- ✅ Verificar que `.env` está no `.gitignore`
- ✅ Rodar `test_setup.py` com sucesso
- ✅ Verificar `git status` - nenhum arquivo sensível listado

## 🔄 Após Upload: Para Quem Clonar

Quem clonar seu repositório fará:

```bash
# Clonar
git clone https://github.com/seu-usuario/IaTrade.git
cd IaTrade

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar credenciais
cp .env.example .env
nano .env  # Preencher com suas credenciais

# Validar setup
python test_setup.py

# Usar
python main.py
```

## 📚 Estrutura do Repositório

```
IaTrade/
├── README.md              ← Visão geral
├── DEPLOYMENT.md          ← Guia de deploy (Oracle)
├── .github/
│   └── ISSUE_TEMPLATE/   ← Templates de issue
├── .env.example           ← Template de credenciais
├── .gitignore             ← Protege .env, logs, dados
├── requirements.txt       ← Dependências
│
├── main.py               ← Bot principal
├── dashboard.py          ← Dashboard Telegram 24h
├── start_bot_24h.py      ← Script para rodar 24h
├── example_integration.py ← Exemplos de uso
├── test_setup.py         ← Validação de setup
│
├── agents/               ← Agentes de IA
│   ├── market_analysis_agent.py
│   ├── risk_management_agent.py
│   └── execution_agent.py
│
├── core/                 ← Núcleo do sistema
│   ├── backtester.py
│   ├── setup_detector.py
│   ├── stop_loss_calculator.py
│   ├── take_profit_calculator.py
│   ├── position_sizing.py
│   └── fibonacci_analyzer.py
│
├── connectors/           ← Conexões externas
│   ├── bybit_connector.py
│   └── data_provider.py
│
├── models/               ← Modelos de dados
│   ├── trade_models.py
│   └── signal_models.py
│
├── utils/                ← Utilidades
│   ├── telegram_notifier.py  ← ✨ NOVO
│   ├── trade_tracker.py      ← ✨ NOVO
│   └── trade_journal.py
│
├── scripts/              ← Scripts utilitários
│   ├── run_backtest_simple.py
│   ├── download_historical_data.py
│   └── simulate_100.py
│
└── logs/                 ← ⚠️ Não fazer commit
```

## 💡 GitHub Best Practices

### Commits Significativos

```bash
# ✅ BOM
git commit -m "Add Telegram notifications for trade alerts"
git commit -m "Fix backtester P&L calculation"

# ❌ RUIM
git commit -m "fix"
git commit -m "updates"
```

### Branches (quando crescer)

```bash
# Criar feature branch
git checkout -b feature/add-websocket-support

# Trabalhar e depois fazer PR
git push origin feature/add-websocket-support
```

### Versioning

```bash
# Adicionar tags para releases
git tag -a v1.0.0 -m "First stable release"
git push origin v1.0.0
```

## 🔗 Links Úteis

- [GitHub Docs](https://docs.github.com/)
- [Git Cheat Sheet](https://www.atlassian.com/git/tutorials/atlassian-git-cheatsheet)
- [GitHub Best Practices](https://github.com/github/gitignore)

## ✅ Próximos Passos Após Upload

1. Adicionar descrição no GitHub
2. Adicionar badges (build, license, etc)
3. Criar Issues para features futuras
4. Setup CI/CD com GitHub Actions (opcional)
5. Documentar releases

---

**Pronto para github!** 🚀
