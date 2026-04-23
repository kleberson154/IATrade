# 🔗 GUIA DE INTEGRAÇÃO COM main.py

Este arquivo mostra como integrar o sistema de notificações Telegram com seu bot principal.

## 📌 Conceito

Seu `main.py` faz:

1. ✅ Detecta setups
2. ✅ Executa trades
3. ❌ (Faltava) Rastrear e notificar

Agora adicionaremos:

- 📊 TradeTracker - Rastreia todas as trades
- 📱 TelegramNotifier - Envia para Telegram
- 🔄 Dashboard - Monitora e reporta

## 🔄 Fluxo de Integração

```
main.py                           dashboard.py (roda em paralelo)
   ↓                                    ↓
Trade happens      ─────→  log/bot_trades.log  ←─ lê e monitora
   ↓                                    ↓
TradeTracker       ─────→  Telegram API ←─────  Notifica
```

## 🛠️ Como Integrar

### Passo 1: Importar no seu main.py

```python
# No início do seu main.py

from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier
from datetime import datetime
import asyncio

# Inicializar
tracker = TradeTracker(log_file="logs/bot_trades.log")
notifier = TelegramNotifier()
```

### Passo 2: Quando Trade Abre (Buy/Sell)

```python
async def on_trade_opened(symbol, direction, entry_price, stop_loss, take_profit, position_size):
    """Chamado quando uma trade é aberta"""

    # Criar objeto Trade
    trade = Trade(
        trade_id=f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        symbol=symbol,
        direction=direction.lower(),  # "long" or "short"
        entry_price=float(entry_price),
        entry_time=datetime.now().isoformat(),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        position_size=float(position_size),
        status="open"
    )

    # Adicionar ao tracker (salva em arquivo e prepara notificação)
    tracker.add_trade(trade)

    # O dashboard detectará e notificará automaticamente
    print(f"✅ Trade aberta: {trade.trade_id}")
```

### Passo 3: Quando Trade Fecha (TP/SL/Manual)

```python
async def on_trade_closed(trade_id, exit_price, exit_reason, pnl_usd):
    """Chamado quando uma trade é fechada"""

    # Atualizar trade no tracker
    tracker.update_trade(
        trade_id=trade_id,
        exit_price=float(exit_price),
        exit_time=datetime.now().isoformat(),
        exit_reason=exit_reason.lower(),  # "tp", "sl", "manual", etc
        pnl_usd=float(pnl_usd),
        status="closed"
    )

    print(f"✅ Trade fechada: {trade_id} | P&L: {pnl_usd}")

    # Dashboard detectará e atualizará automaticamente
```

## 📋 Exemplo Completo (Como Integrável)

```python
# ===== main.py (seu bot principal) =====

import asyncio
from datetime import datetime
from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier

class MyTradingBot:
    def __init__(self):
        self.tracker = TradeTracker(log_file="logs/bot_trades.log")
        self.notifier = TelegramNotifier()
        self.trades = {}  # Rastreamento interno

    async def start_bot(self):
        """Iniciar bot"""
        # Enviar startup msg
        await self.notifier.send_startup_message({
            "version": "1.0.0",
            "mode": "demo",
            "symbols": ["BTCUSDT", "ETHUSDT"]
        })

        # Loop principal
        while True:
            await self.monitor_market()
            await asyncio.sleep(1)

    async def monitor_market(self):
        """Seu código atual de detecção de setups"""
        # ... seu código de market analysis ...

        # Quando detectar setup
        if setup_detected:
            await self.open_trade(
                symbol="BTCUSDT",
                direction="long",
                entry=45000.0,
                sl=44500.0,
                tp=46000.0,
                size=0.1
            )

    async def open_trade(self, symbol, direction, entry, sl, tp, size):
        """Abrir trade - INTEGRAÇÃO!"""

        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Criar objeto trade
        trade = Trade(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry,
            entry_time=datetime.now().isoformat(),
            stop_loss=sl,
            take_profit=tp,
            position_size=size,
            status="open"
        )

        # Adicionar ao tracker (salva e notifica via dashboard)
        self.tracker.add_trade(trade)

        # Rastreamento interno
        self.trades[trade_id] = trade

        print(f"📈 Trade aberta: {trade_id}")

    async def check_exit(self):
        """Verificar se TP/SL foi atingido"""
        for trade_id, trade in list(self.trades.items()):
            if trade.status == "closed":
                continue

            # ... seu código de verificação de TP/SL ...

            if tp_atingido:
                await self.close_trade(
                    trade_id=trade_id,
                    exit_price=46000.0,
                    reason="tp",
                    pnl=100.0
                )

    async def close_trade(self, trade_id, exit_price, reason, pnl):
        """Fechar trade - INTEGRAÇÃO!"""

        # Atualizar tracker
        self.tracker.update_trade(
            trade_id=trade_id,
            exit_price=exit_price,
            exit_time=datetime.now().isoformat(),
            exit_reason=reason,
            pnl_usd=pnl,
            status="closed"
        )

        # Remover de rastreamento interno
        if trade_id in self.trades:
            del self.trades[trade_id]

        print(f"📊 Trade fechada: {trade_id} | P&L: ${pnl}")

# Rodar
if __name__ == "__main__":
    bot = MyTradingBot()
    asyncio.run(bot.start_bot())
```

## 🔀 Se seu main.py já existe

### Scenario: main.py com execution_agent

```python
# Em seu execution_agent.py ou main.py

from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier

class ExecutionAgent:
    def __init__(self):
        self.tracker = TradeTracker()
        self.notifier = TelegramNotifier()

    def execute_trade(self, trade_data):
        """Executar trade na exchange"""

        # Seu código Bybit...
        response = self.bybit.place_order(...)

        # Criar objeto trade para rastrear
        trade = Trade(
            trade_id=f"{trade_data['symbol']}_{response['order_id']}",
            symbol=trade_data['symbol'],
            direction=trade_data['direction'],
            entry_price=trade_data['entry'],
            entry_time=datetime.now().isoformat(),
            stop_loss=trade_data['stop_loss'],
            take_profit=trade_data['take_profit'],
            position_size=trade_data['size'],
            status="open"
        )

        # Adicionar ao tracker
        self.tracker.add_trade(trade)

        return response
```

### Scenario: main.py com WebSocket

```python
# Em seu websocket listener

from utils.trade_tracker import TradeTracker

tracker = TradeTracker()

@on_trade_event
def on_trade_executed(event):
    """Escuta eventos da Bybit"""
    if event['type'] == 'ORDER_OPENED':
        trade = Trade(
            trade_id=event['order_id'],
            symbol=event['symbol'],
            # ... preencher outros campos ...
            status="open"
        )
        tracker.add_trade(trade)

    elif event['type'] == 'ORDER_CLOSED':
        tracker.update_trade(
            trade_id=event['order_id'],
            exit_price=event['exit_price'],
            exit_reason=event['reason'],
            pnl_usd=event['pnl'],
            status="closed"
        )
```

## 🚀 Arquitetura com Dashboard

```
┌──────────────────────────────────────────────┐
│              Seu main.py                      │
│  (roda em paralelo com dashboard.py)         │
├──────────────────────────────────────────────┤
│                                               │
│  while True:                                  │
│    - Detectar setups                         │
│    - Executar trades                         │
│    - Atualizar TradeTracker                 │
│    - await tracker.add_trade(trade)         │
│    - await tracker.update_trade(...)        │
│                                               │
│  logs/bot_trades.log ← salva trades          │
│           ↓ lê arquivo                       │
│     dashboard.py (rodando em outro processo) │
│           ↓                                   │
│     Detecta novas trades                     │
│     Envia notificações Telegram              │
│           ↓ a cada 2h                        │
│     Calcula e reporta estatísticas           │
│                                               │
└──────────────────────────────────────────────┘
```

## 📊 Exemplo: Seu main.py Atual

Se seu `main.py` atual faz:

```python
# ANTES (sem tracker)
def execute_trade(symbol, entry, sl, tp, size):
    response = bybit.place_order(symbol, "long", entry, sl, tp, size)
    print(f"Trade executada: {response}")
```

**DEPOIS (com tracker):**

```python
# DEPOIS (com tracker)
def execute_trade(symbol, entry, sl, tp, size):
    response = bybit.place_order(symbol, "long", entry, sl, tp, size)

    # ADICIONAR ISTO:
    trade = Trade(
        trade_id=response['order_id'],
        symbol=symbol,
        direction="long",
        entry_price=entry,
        entry_time=datetime.now().isoformat(),
        stop_loss=sl,
        take_profit=tp,
        position_size=size,
        status="open"
    )
    tracker.add_trade(trade)  # ← Uma linha!

    print(f"Trade executada: {response}")
```

## 🔧 Dados Necessários

O tracker precisa de:

| Campo         | Tipo    | Exemplo                                  |
| ------------- | ------- | ---------------------------------------- |
| trade_id      | str     | "BTCUSDT_20240120_150000"                |
| symbol        | str     | "BTCUSDT"                                |
| direction     | str     | "long" ou "short"                        |
| entry_price   | float   | 45000.0                                  |
| entry_time    | str ISO | "2024-01-20T15:00:00"                    |
| stop_loss     | float   | 44500.0                                  |
| take_profit   | float   | 46000.0                                  |
| position_size | float   | 0.1                                      |
| status        | str     | "open" ou "closed"                       |
| exit_price    | float   | 46000.0 (apenas se closed)               |
| exit_time     | str ISO | "2024-01-20T15:30:00" (apenas se closed) |
| exit_reason   | str     | "tp", "sl", "manual"                     |
| pnl_usd       | float   | 100.0 (apenas se closed)                 |
| pnl_percent   | float   | 0.22 (opcional)                          |

## ✅ Checklist de Integração

- [ ] Importar TradeTracker e TelegramNotifier
- [ ] Inicializar no **init** ou startup
- [ ] Criar Trade object quando trade abre
- [ ] Chamar tracker.add_trade(trade)
- [ ] Chamar tracker.update_trade quando fecha
- [ ] Rodar dashboard.py em paralelo
- [ ] Testar com example_integration.py
- [ ] Validar com test_setup.py
- [ ] Receber notificações no Telegram

## 🎯 Resumo

**Antes:**

- Bot roda sozinho
- Sem visibilidade remota
- Sem histórico

**Depois:**

- Bot roda + rastreia trades
- Notificações em tempo real
- Histórico completo em arquivo
- Dashboard monitora 24/7
- Relatórios automáticos

**Esforço:** ~5 minutos de integração

---

**Perguntas?** Consulte `example_integration.py` para exemplos mais detalhados!
