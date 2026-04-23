#!/usr/bin/env python3
"""
Exemplo: Integração Completa - Bybit Sync + TradeTracker + Telegram Dashboard

Este script mostra como:
1. Buscar histórico de trades da Bybit
2. Registrar no TradeTracker
3. Enviar notificações via Telegram

Uso:
    python example_sync_with_telegram.py
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from connectors.bybit_connector import BybitConnector
from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier


async def sync_and_notify():
    """Sincroniza trades da Bybit e notifica via Telegram"""
    
    print("\n" + "=" * 70)
    print("SINCRONIZAÇÃO BYBIT + TELEGRAM NOTIFIER")
    print("=" * 70)
    
    # Inicializar componentes
    connector = BybitConnector(mode="demo")
    tracker = TradeTracker(log_file="logs/bot_trades.log")
    notifier = TelegramNotifier()
    
    print("\n[1] BUSCANDO DADOS DA BYBIT...")
    
    # Buscar dados
    account = connector.get_account_info()
    closed_orders = connector.get_closed_orders(symbol="BTCUSDT", limit=5)
    trade_history = connector.get_trade_history(symbol="BTCUSDT", limit=5)
    
    print(f"   [OK] Saldo: ${account.get('wallet_balance', 0)}")
    print(f"   [OK] Closed Orders: {len(closed_orders)}")
    print(f"   [OK] Trade History: {len(trade_history)}")
    
    print("\n[2] REGISTRANDO TRADES NO TRACKER...")
    
    # Processar e registrar trades
    registered_count = 0
    
    for trade_data in trade_history[:3]:  # Primeiros 3 trades
        try:
            # Extrair dados
            exec_id = trade_data.get("execId")
            symbol = trade_data.get("symbol", "BTCUSDT")
            side = trade_data.get("side", "Buy").lower()
            price = float(trade_data.get("execPrice", 0))
            qty = float(trade_data.get("execQty", 0))
            fee = float(trade_data.get("tradingFee", 0))
            exec_time = int(trade_data.get("execTime", 0))
            
            # Converter timestamp (millisegundos → segundos)
            trade_time = datetime.fromtimestamp(exec_time / 1000).isoformat()
            
            # Criar objeto Trade com SL e TP simulados
            sl_distance = price * 0.001  # 0.1% de SL
            tp_distance = price * 0.002  # 0.2% de TP
            
            trade = Trade(
                trade_id=exec_id,
                symbol=symbol,
                direction=side,
                entry_price=price,
                entry_time=trade_time,
                stop_loss=price - sl_distance if side == "long" else price + sl_distance,
                take_profit=price + tp_distance if side == "long" else price - tp_distance,
                position_size=qty,
                exit_price=price,
                exit_time=trade_time,
                exit_reason="filled",
                pnl_usd=qty * price - fee,  # Valor - fee
                pnl_percent=((qty * price - fee) / (qty * price)) * 100 if qty * price > 0 else 0,
                status="closed",
            )
            
            # Adicionar ao tracker
            tracker.add_trade(trade)
            registered_count += 1
            
            print(f"   [OK] Trade registrada: {exec_id}")
        
        except Exception as e:
            print(f"   [ERROR] Erro ao registrar {trade_data.get('execId')}: {e}")
    
    print(f"   Total registradas: {registered_count}")
    
    print("\n[3] CALCULANDO ESTATÍSTICAS...")
    
    # Buscar trades do tracker
    trades = tracker.trades if hasattr(tracker, 'trades') else []
    
    # Calcular estatísticas manualmente
    wins = sum(1 for t in trades if t.pnl_usd > 0)
    losses = sum(1 for t in trades if t.pnl_usd < 0)
    total_pnl = sum(t.pnl_usd for t in trades)
    win_rate = (wins / len(trades) * 100) if len(trades) > 0 else 0
    
    print(f"   Total de Trades: {len(trades)}")
    print(f"   Ganhadoras: {wins}")
    print(f"   Perdedoras: {losses}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   P&L Total: ${total_pnl:.2f}")
    
    print("\n[4] ENVIANDO NOTIFICAÇÃO TELEGRAM...")
    
    # Preparar mensagem
    buy_trades = sum(1 for t in trades if t.direction == 'buy')
    sell_trades = sum(1 for t in trades if t.direction == 'sell')
    avg_pnl = (total_pnl / wins) if wins > 0 else 0
    
    message = f"""
[RELATORIO] SINCRONIZAÇÃO BYBIT COMPLETA

[SALDO] ${account.get('wallet_balance', 0)}

[TRADES SINCRONIZADAS]
Total: {registered_count} trades
Win Rate: {win_rate:.1f}%
P&L: ${total_pnl:.2f}

[DETALHE]
Buys: {buy_trades}
Sells: {sell_trades}
Avg P&L: ${avg_pnl:.2f}

Sincronizado em: {datetime.now().strftime('%H:%M:%S')}
    """
    
    result = await notifier.send_message(message)
    print(f"   [OK] Mensagem enviada!")
    
    print("\n[5] EXPORTANDO PARA CSV...")
    
    csv_file = "exports/sync_trades.csv"
    tracker.export_to_csv(csv_file)
    print(f"   [OK] Arquivo: {csv_file}")
    
    print("\n" + "=" * 70)
    print("[OK] SINCRONIZAÇÃO COMPLETA!")
    print("=" * 70)
    
    return True


async def continuous_sync(interval_hours: int = 1):
    """Sincronização contínua em background"""
    import time
    
    print(f"\n[SYNC] Sincronização contínua a cada {interval_hours} hora(s)")
    print("   Pressione Ctrl+C para parar\n")
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Sincronizando...")
            
            success = await sync_and_notify()
            
            if success:
                print(f"   [OK] Próxima sincronização em {interval_hours}h")
            
            # Aguardar próximo ciclo
            await asyncio.sleep(interval_hours * 3600)
    
    except KeyboardInterrupt:
        print("\n\n[STOP] Sincronização interrompida pelo usuário")


def main():
    """Menu principal"""
    print("\n" + "=" * 70)
    print("INTEGRAÇÃO BYBIT SYNC + TELEGRAM NOTIFIER")
    print("=" * 70)
    print("\nOpções:")
    print("  1. Sincronizar uma vez")
    print("  2. Sincronização contínua (a cada 1h)")
    print("  3. Sincronização contínua (a cada 30min)")
    print("  4. Ver histórico local")
    print("  5. Sair")
    
    choice = input("\nEscolha uma opção (1-5): ").strip()
    
    if choice == "1":
        # Sincronizar uma vez
        asyncio.run(sync_and_notify())
    
    elif choice == "2":
        # Contínua a cada 1h
        asyncio.run(continuous_sync(interval_hours=1))
    
    elif choice == "3":
        # Contínua a cada 30min
        asyncio.run(continuous_sync(interval_hours=0.5))
    
    elif choice == "4":
        # Ver histórico
        tracker = TradeTracker()
        trades = tracker.trades if hasattr(tracker, 'trades') else []
        
        # Calcular estatísticas
        wins = sum(1 for t in trades if t.pnl_usd > 0)
        losses = sum(1 for t in trades if t.pnl_usd < 0)
        total_pnl = sum(t.pnl_usd for t in trades)
        win_rate = (wins / len(trades) * 100) if len(trades) > 0 else 0
        
        print("\n" + "=" * 70)
        print("HISTÓRICO LOCAL DE TRADES")
        print("=" * 70)
        print(f"\nTotal de Trades: {len(trades)}")
        print(f"Ganhadoras: {wins}")
        print(f"Perdedoras: {losses}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"P&L Total: ${total_pnl:.2f}")
        
        if trades:
            print("\nÚltimas 5 trades:")
            for trade in trades[-5:]:
                print(f"  - {trade.trade_id}: {trade.direction.upper()} {trade.position_size} @ ${trade.entry_price}")
    
    elif choice == "5":
        print("Saindo...")
        return
    
    else:
        print("[ERROR] Opção inválida")


if __name__ == "__main__":
    main()
