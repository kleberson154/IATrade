#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
start_bot_24h.py - Inicia o bot para rodar 24h na Oracle Free Tier
"""

import subprocess
import sys
import os
import signal
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(str(log_dir / 'bot_manager.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BotManager")


class BotManager:
    """Gerencia a execução do bot 24h"""
    
    def __init__(self):
        """Inicializa o gerenciador"""
        self.bot_process = None
        self.dashboard_process = None
        logger.info("BotManager inicializado")
    
    def start_bot(self):
        """Inicia o bot principal"""
        try:
            logger.info("Iniciando bot principal...")
            
            # Verificar se arquivo principal existe
            if not Path("main.py").exists():
                logger.error("main.py não encontrado")
                return False
            
            # Iniciar processo
            self.bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info(f"Bot iniciado com PID: {self.bot_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar bot: {e}")
            return False
    
    def start_dashboard(self):
        """Inicia o dashboard"""
        try:
            logger.info("Iniciando dashboard...")
            
            # Verificar se arquivo existe
            if not Path("dashboard.py").exists():
                logger.error("dashboard.py não encontrado")
                return False
            
            # Iniciar processo
            self.dashboard_process = subprocess.Popen(
                [sys.executable, "dashboard.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            logger.info(f"Dashboard iniciado com PID: {self.dashboard_process.pid}")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar dashboard: {e}")
            return False
    
    def check_processes(self):
        """Verifica se os processos estão rodando"""
        bot_ok = self.bot_process is not None and self.bot_process.poll() is None
        dashboard_ok = self.dashboard_process is not None and self.dashboard_process.poll() is None
        
        if not bot_ok:
            logger.warning("Bot não está rodando!")
        if not dashboard_ok:
            logger.warning("Dashboard não está rodando!")
        
        return bot_ok and dashboard_ok
    
    def restart_if_needed(self):
        """Reinicia processos se necessário"""
        if self.bot_process is not None and self.bot_process.poll() is not None:
            logger.warning("Bot foi encerrado, reiniciando...")
            self.start_bot()
        
        if self.dashboard_process is not None and self.dashboard_process.poll() is not None:
            logger.warning("Dashboard foi encerrado, reiniciando...")
            self.start_dashboard()
    
    def start(self):
        """Inicia o bot manager"""
        try:
            logger.info("="*80)
            logger.info("INICIANDO BOT 24H - ORACLE FREE TIER")
            logger.info("="*80)
            
            # Criar diretórios necessários
            Path("logs").mkdir(exist_ok=True)
            Path("data").mkdir(exist_ok=True)
            Path("exports").mkdir(exist_ok=True)
            
            # Iniciar processos
            if not self.start_bot():
                logger.error("Falha ao iniciar bot")
                return
            
            time.sleep(2)  # Aguardar bot iniciar
            
            if not self.start_dashboard():
                logger.error("Falha ao iniciar dashboard")
                return
            
            logger.info("Sistema iniciado com sucesso!")
            logger.info("Bot PID: {}".format(self.bot_process.pid))
            logger.info("Dashboard PID: {}".format(self.dashboard_process.pid))
            
            # Loop de monitoramento
            self.monitor_loop()
        
        except KeyboardInterrupt:
            logger.info("Interrupção do usuário")
            self.shutdown()
        except Exception as e:
            logger.error(f"Erro fatal: {e}", exc_info=True)
            self.shutdown()
    
    def monitor_loop(self):
        """Loop de monitoramento contínuo"""
        logger.info("Iniciando loop de monitoramento")
        
        try:
            while True:
                # Verificar processos a cada 60 segundos
                if not self.check_processes():
                    logger.warning("Detectado processo encerrado")
                    self.restart_if_needed()
                
                # Log de status a cada 1 hora
                time.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("Loop de monitoramento interrompido")
        except Exception as e:
            logger.error(f"Erro no loop de monitoramento: {e}")
    
    def shutdown(self):
        """Encerra o bot e o dashboard"""
        logger.info("Encerrando sistema...")
        
        try:
            # Encerrar bot
            if self.bot_process is not None and self.bot_process.poll() is None:
                logger.info(f"Encerrando bot (PID: {self.bot_process.pid})")
                self.bot_process.terminate()
                try:
                    self.bot_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Bot não respondeu, forçando encerramento")
                    self.bot_process.kill()
            
            # Encerrar dashboard
            if self.dashboard_process is not None and self.dashboard_process.poll() is None:
                logger.info(f"Encerrando dashboard (PID: {self.dashboard_process.pid})")
                self.dashboard_process.terminate()
                try:
                    self.dashboard_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Dashboard não respondeu, forçando encerramento")
                    self.dashboard_process.kill()
            
            logger.info("Sistema encerrado")
        except Exception as e:
            logger.error(f"Erro ao encerrar: {e}")


def signal_handler(sig, frame):
    """Tratador de sinais"""
    logger.info(f"Sinal recebido: {sig}")
    sys.exit(0)


if __name__ == "__main__":
    # Configurar tratamento de sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar gerenciador
    manager = BotManager()
    manager.start()
