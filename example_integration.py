"""
example_integration.py - Exemplo de integração com o sistema de notificações
"""

import asyncio
from datetime import datetime
from utils.trade_tracker import Trade, TradeTracker
from utils.telegram_notifier import TelegramNotifier


async def example_trade_workflow():
    """Exemplo de workflow completo com notificações"""
    
    # Inicializar tracker e notifier
    tracker = TradeTracker(log_file="logs/bot_trades.log")
    notifier = TelegramNotifier()
    
    print("=" * 80)
    print("EXEMPLO: Integração com Sistema de Notificações")
    print("=" * 80)
    
    # === PASSO 1: Abrir uma nova trade ===
    print("\n1️⃣  Abrindo nova trade...")
    
    new_trade = Trade(
        trade_id="BTCUSDT_20240120_150000",
        symbol="BTCUSDT",
        direction="long",
        entry_price=45000.0,
        entry_time=datetime.now().isoformat(),
        stop_loss=44500.0,
        take_profit=46000.0,
        position_size=0.1,
        status="open"
    )
    
    # Adicionar ao tracker
    tracker.add_trade(new_trade)
    print(f"✅ Trade {new_trade.trade_id} adicionada")
    
    # Enviar notificação
    trade_data = {
        'symbol': new_trade.symbol,
        'direction': new_trade.direction,
        'entry_price': new_trade.entry_price,
        'stop_loss': new_trade.stop_loss,
        'take_profit': new_trade.take_profit,
        'position_size': new_trade.position_size,
        'rr_ratio': new_trade.calculate_rr_ratio(),
        'time': new_trade.entry_time
    }
    
    print("📤 Enviando notificação de trade...")
    result = await notifier.send_trade_notification(trade_data)
    print(f"Resultado: {'✅ Enviado' if result else '❌ Falha'}")
    
    # === PASSO 2: Atualizar a trade (simulando que foi fechada em TP) ===
    print("\n2️⃣  Atualizando trade (fechada em TP)...")
    
    await asyncio.sleep(2)  # Simular tempo passando
    
    tracker.update_trade(
        new_trade.trade_id,
        exit_price=46000.0,
        exit_time=datetime.now().isoformat(),
        exit_reason="tp",
        pnl_usd=100.0,
        pnl_percent=2.22,
        status="closed"
    )
    print("✅ Trade atualizada")
    
    # === PASSO 3: Calcular e enviar estatísticas ===
    print("\n3️⃣  Calculando e enviando estatísticas...")
    
    stats = tracker.calculate_stats()
    stats['period'] = 'Últimas 2 horas'
    
    print(f"Stats calculadas:")
    print(f"  - Total de trades: {stats['total_trades']}")
    print(f"  - Ganhadoras: {stats['wins']}")
    print(f"  - Perdedoras: {stats['losses']}")
    print(f"  - Win Rate: {stats['win_rate']:.1f}%")
    print(f"  - Total P&L: ${stats['total_pnl']:.2f}")
    
    print("\n📤 Enviando relatório...")
    result = await notifier.send_stats_report(stats)
    print(f"Resultado: {'✅ Enviado' if result else '❌ Falha'}")
    
    # === PASSO 4: Enviar alerta de erro (opcional) ===
    print("\n4️⃣  Enviando alerta de exemplo...")
    
    result = await notifier.send_error_alert(
        "Exemplo de erro: Conexão perdida com Bybit",
        context="Retry automático em 30s"
    )
    print(f"Resultado: {'✅ Enviado' if result else '❌ Falha'}")
    
    # === PASSO 5: Exportar trades ===
    print("\n5️⃣  Exportando trades...")
    
    tracker.export_to_csv(filename="example_trades.csv")
    print("✅ Trades exportadas para exports/example_trades.csv")
    
    print("\n" + "=" * 80)
    print("✅ EXEMPLO CONCLUÍDO COM SUCESSO")
    print("=" * 80)


async def example_continuous_monitoring():
    """Exemplo de monitoramento contínuo"""
    
    print("\n" + "=" * 80)
    print("EXEMPLO 2: Monitoramento Contínuo")
    print("=" * 80)
    
    tracker = TradeTracker()
    notifier = TelegramNotifier()
    
    print("\nMonitorando trades a cada 5 segundos...")
    print("(Este é um exemplo - pressione Ctrl+C para parar)\n")
    
    try:
        for i in range(3):  # 3 iterações para demo
            # Adicionar trade aleatória
            import random
            
            trade_id = f"DEMO_{i:04d}"
            symbol = random.choice(['BTCUSDT', 'ETHUSDT', 'LINKUSDT'])
            direction = random.choice(['long', 'short'])
            entry_price = random.uniform(1000, 50000)
            
            trade = Trade(
                trade_id=trade_id,
                symbol=symbol,
                direction=direction,
                entry_price=entry_price,
                entry_time=datetime.now().isoformat(),
                stop_loss=entry_price * 0.985 if direction == 'long' else entry_price * 1.015,
                take_profit=entry_price * 1.015 if direction == 'long' else entry_price * 0.985,
                position_size=random.uniform(0.01, 0.1),
                status="open"
            )
            
            tracker.add_trade(trade)
            print(f"\n✅ Trade #{i+1} adicionada: {trade_id}")
            print(f"   {direction.upper()} {symbol} @ ${entry_price:.2f}")
            
            # Aguardar
            await asyncio.sleep(5)
        
        # Relatório final
        stats = tracker.calculate_stats()
        print(f"\n📊 Relatório Final:")
        print(f"   Total: {stats['total_trades']} trades")
        print(f"   Winrate: {stats['win_rate']:.1f}%")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoramento interrompido")


async def main():
    """Função principal"""
    
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "EXEMPLOS DE INTEGRAÇÃO".center(58) + " " * 20 + "║")
    print("║" + " " * 20 + "Sistema de Notificações Telegram".center(58) + " " * 20 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Escolher exemplo
    print("\nEscolha um exemplo:")
    print("1. Workflow completo (abrir, atualizar, reportar)")
    print("2. Monitoramento contínuo")
    
    choice = input("\nOpção (1 ou 2): ").strip()
    
    if choice == "1":
        await example_trade_workflow()
    elif choice == "2":
        await example_continuous_monitoring()
    else:
        print("Opção inválida")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Exemplo interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
