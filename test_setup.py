#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_setup.py - Valida que tudo está configurado corretamente
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

def check_python_version():
    """Verifica versão do Python"""
    print("🔍 Verificando Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} OK")
        return True
    else:
        print(f"  ❌ Python 3.8+ necessário (você tem {version.major}.{version.minor})")
        return False


def check_env_file():
    """Verifica se .env existe e está preenchido"""
    print("\n🔍 Verificando arquivo .env...")
    
    if not Path(".env").exists():
        print("  ❌ .env não encontrado")
        print("  💡 Copie .env.example para .env e preencha as credenciais")
        return False
    
    load_dotenv()
    
    required_vars = {
        'TELEGRAM_TOKEN': 'Token do Telegram',
        'TELEGRAM_CHAT_ID': 'Chat ID do Telegram',
        'BYBIT_API_KEY': 'Chave API Bybit',
        'BYBIT_API_SECRET': 'Secret API Bybit',
    }
    
    all_ok = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value and value != 'seu_token_aqui' and value != 'sua_chave_aqui':
            print(f"  ✅ {var}: Configurado")
        else:
            print(f"  ❌ {var}: Não configurado ou padrão")
            all_ok = False
    
    return all_ok


def check_directories():
    """Verifica se os diretórios existem"""
    print("\n🔍 Verificando diretórios...")
    
    required_dirs = ['logs', 'data', 'exports', 'models']
    all_ok = True
    
    for dir_name in required_dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ⚠️  {dir_name}/ - Criando...")
            path.mkdir(exist_ok=True)
    
    return True


def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    print("\n🔍 Verificando dependências...")
    
    required_packages = {
        'requests': 'Requests HTTP',
        'dotenv': 'Python-dotenv',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'aiohttp': 'Aiohttp',
    }
    
    all_ok = True
    for package, desc in required_packages.items():
        try:
            __import__(package)
            print(f"  ✅ {desc}")
        except ImportError:
            print(f"  ❌ {desc} - Execute: pip install {package}")
            all_ok = False
    
    return all_ok


def check_files():
    """Verifica se os arquivos principais existem"""
    print("\n🔍 Verificando arquivos...")
    
    required_files = {
        'main.py': 'Bot principal',
        'dashboard.py': 'Dashboard Telegram',
        'start_bot_24h.py': 'Script 24h',
        'utils/telegram_notifier.py': 'Notificador Telegram',
        'utils/trade_tracker.py': 'Rastreador de trades',
        'core/backtester.py': 'Backtester',
        'core/setup_detector.py': 'Detector de setups',
    }
    
    all_ok = True
    for file, desc in required_files.items():
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Não encontrado")
            all_ok = False
    
    return all_ok


async def test_telegram():
    """Testa conexão com Telegram"""
    print("\n🔍 Testando Telegram...")
    
    try:
        from utils.telegram_notifier import TelegramNotifier
        
        notifier = TelegramNotifier()
        result = await notifier.send_message("✅ Teste de conexão do IaTrade!")
        
        if result:
            print("  ✅ Telegram conectado com sucesso")
            return True
        else:
            print("  ❌ Falha ao enviar mensagem para Telegram")
            return False
    except Exception as e:
        print(f"  ❌ Erro ao testar Telegram: {e}")
        return False


async def main():
    """Executa todos os testes"""
    
    print("\n" + "=" * 80)
    print("VALIDAÇÃO DE SETUP - IaTrade".center(80))
    print("=" * 80)
    
    checks = [
        ("Python", check_python_version()),
        ("Arquivos", check_files()),
        ("Diretórios", check_directories()),
        ("Dependências", check_dependencies()),
        (".env", check_env_file()),
    ]
    
    # Teste assíncrono
    try:
        telegram_ok = await test_telegram()
        checks.append(("Telegram", telegram_ok))
    except Exception as e:
        print(f"\n⚠️  Teste de Telegram pulado: {e}")
        checks.append(("Telegram", False))
    
    # Resumo
    print("\n" + "=" * 80)
    print("RESUMO".center(80))
    print("=" * 80)
    
    for check_name, result in checks:
        status = "✅ OK" if result else "❌ ERRO"
        print(f"{check_name:20} {status}")
    
    # Resultado final
    all_ok = all(result for _, result in checks)
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ TUDO OK - SISTEMA PRONTO PARA USAR!".center(80))
        print("\n💡 Próximos passos:")
        print("  1. python example_integration.py  (entender a integração)")
        print("  2. python main.py                 (iniciar bot)")
        print("  3. python dashboard.py            (dashboard separado)")
        print("  4. python start_bot_24h.py        (rodar continuamente)")
    else:
        print("❌ PROBLEMAS ENCONTRADOS - VEJA ACIMA".center(80))
        print("\n💡 Para resolver:")
        print("  1. Verificar erros acima")
        print("  2. Executar: pip install -r requirements.txt")
        print("  3. Preencher .env com suas credenciais")
        print("  4. Rodar este script novamente")
    print("=" * 80 + "\n")
    
    return 0 if all_ok else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Teste interrompido")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        sys.exit(1)
