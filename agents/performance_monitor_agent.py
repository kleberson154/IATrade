"""
Agente de Monitoramento de Performance
Rastreia: Expectancy, Win Rate, Average Win/Loss, Variance
Essencial do artigo: "Only the series matters"
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from models.trade_models import Trade, PerformanceStats
from config.settings import TRACK_EXPECTANCY, MIN_ACCEPTABLE_EXPECTANCY, REVIEW_PERIOD_TRADES


class PerformanceMonitorAgent:
    """
    Agente responsável por:
    - Calcular expectancy: E = W x R - (1-W)
    - Rastrear win rate, avg win, avg loss
    - Detectar mudanças de regime (drift)
    - Alertar se performance cai abaixo de mínimo
    - Revisar sistema regularmente
    """
    
    def __init__(self, agent_id: str = "PERF-001"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        
        self.all_trades: List[Trade] = []
        self.performance_history: List[PerformanceStats] = []
        
        self.current_stats = PerformanceStats()
        self.cumulative_pnl = 0.0
    
    def add_closed_trade(self, trade: Trade):
        """Adiciona trade fechada para análise"""
        if not trade.is_closed:
            self.logger.warning(f"Trade {trade.id} não está fechada")
            return
        
        self.all_trades.append(trade)
        self.cumulative_pnl += trade.pnl_usdt
        
        # Recalcula stats
        self._recalculate_stats()
        
        self.logger.info(
            f"Trade adicionada | PnL: ${trade.pnl_usdt:+.2f} | "
            f"Cumulative: ${self.cumulative_pnl:+.2f} | "
            f"Expectancy: {self.current_stats.expectancy:+.0%}"
        )
    
    def _recalculate_stats(self):
        """Recalcula todas as estatísticas"""
        new_stats = PerformanceStats()
        new_stats.calculate(self.all_trades)
        
        self.current_stats = new_stats
        self.performance_history.append(new_stats)
        
        # Mantém histórico do tamanho gerenciável
        if len(self.performance_history) > 200:
            self.performance_history = self.performance_history[-200:]
    
    def check_expectancy(self) -> Dict:
        """
        Verifica expectancy e alertas
        E = W x R - (1-W) onde R = avg_win / avg_loss
        """
        result = {
            "expectancy": self.current_stats.expectancy,
            "expectancy_percent": self.current_stats.expectancy_percent,
            "status": "UNKNOWN",
            "alert": None,
        }
        
        if self.current_stats.total_trades < 10:
            result["status"] = "INSUFFICIENT_DATA"
            result["alert"] = f"Apenas {self.current_stats.total_trades} trades (mínimo: 10)"
            return result
        
        if self.current_stats.expectancy < 0:
            result["status"] = "NEGATIVE_EXPECTANCY"
            result["alert"] = f"⚠️ EXPECTANCY NEGATIVA: {self.current_stats.expectancy:.0%}"
            return result
        
        if self.current_stats.expectancy < MIN_ACCEPTABLE_EXPECTANCY:
            result["status"] = "BELOW_MINIMUM"
            result["alert"] = f"⚠️ Expectancy muito baixa: {self.current_stats.expectancy:.0%} (min: {MIN_ACCEPTABLE_EXPECTANCY:.0%})"
            return result
        
        result["status"] = "POSITIVE"
        result["alert"] = f"✓ Expectancy positiva: {self.current_stats.expectancy:+.0%}"
        
        return result
    
    def check_win_rate(self) -> Dict:
        """Valida win rate"""
        result = {
            "win_rate": self.current_stats.win_rate,
            "winning_trades": self.current_stats.winning_trades,
            "losing_trades": self.current_stats.losing_trades,
            "status": "UNKNOWN",
            "alert": None,
        }
        
        if self.current_stats.total_trades < 10:
            result["status"] = "INSUFFICIENT_DATA"
            return result
        
        # Win rate baixa é OK se RR for boa
        if self.current_stats.win_rate < 0.40:
            # Precisa ter RR excelente
            if self.current_stats.rr_ratio < 2.5:
                result["status"] = "WEAK_SETUP"
                result["alert"] = f"⚠️ Win rate {self.current_stats.win_rate:.0%} COM RR baixo {self.current_stats.rr_ratio:.2f}x"
            else:
                result["status"] = "ACCEPTABLE"
                result["alert"] = f"Win rate baixa ({self.current_stats.win_rate:.0%}) mas RR alta ({self.current_stats.rr_ratio:.2f}x) ✓"
        else:
            result["status"] = "GOOD"
            result["alert"] = f"Win rate saudável: {self.current_stats.win_rate:.0%}"
        
        return result
    
    def check_rr_ratio(self) -> Dict:
        """Valida RR ratio (Average Win / Average Loss)"""
        result = {
            "rr_ratio": self.current_stats.rr_ratio,
            "avg_win": self.current_stats.avg_win,
            "avg_loss": self.current_stats.avg_loss,
            "status": "UNKNOWN",
            "alert": None,
        }
        
        from config.settings import MIN_RR_RATIO
        
        if self.current_stats.total_trades < 10:
            result["status"] = "INSUFFICIENT_DATA"
            return result
        
        if self.current_stats.rr_ratio < MIN_RR_RATIO:
            result["status"] = "BELOW_MINIMUM"
            result["alert"] = f"⚠️ RR baixo: {self.current_stats.rr_ratio:.2f}x (min: {MIN_RR_RATIO}x)"
        else:
            result["status"] = "ACCEPTABLE"
            result["alert"] = f"✓ RR: {self.current_stats.rr_ratio:.2f}x"
        
        return result
    
    def get_performance_summary(self) -> str:
        """Retorna resumo de performance"""
        if not self.all_trades:
            return "Nenhuma trade fechada ainda"
        
        return (
            f"Total: {self.current_stats.total_trades} trades | "
            f"Wins: {self.current_stats.winning_trades} | "
            f"Losses: {self.current_stats.losing_trades} | "
            f"Win Rate: {self.current_stats.win_rate:.0%} | "
            f"Avg Win: ${self.current_stats.avg_win:.2f} | "
            f"Avg Loss: ${self.current_stats.avg_loss:.2f} | "
            f"RR: {self.current_stats.rr_ratio:.2f}x | "
            f"Expectancy: {self.current_stats.expectancy:+.0%} | "
            f"Total PnL: ${self.current_stats.total_pnl:+.2f}"
        )
    
    def detect_regime_change(self) -> Optional[str]:
        """
        Detecta se há mudança de regime (performance piora)
        Útil para alertar quando algo está errado
        """
        if len(self.performance_history) < 10:
            return None
        
        # Compara expectancy: últimas 10 vs 10 anteriores
        recent = self.performance_history[-10:]
        older = self.performance_history[-20:-10] if len(self.performance_history) >= 20 else recent
        
        recent_avg = sum(s.expectancy for s in recent) / len(recent)
        older_avg = sum(s.expectancy for s in older) / len(older)
        
        if recent_avg < older_avg - 0.10:  # Piora de 10%
            return f"⚠️ REGIME CHANGE DETECTADO: Expectancy caiu de {older_avg:+.0%} para {recent_avg:+.0%}"
        
        return None
    
    def should_review_system(self) -> bool:
        """Indica se deve revisar o sistema (a cada N trades)"""
        return (self.current_stats.total_trades % REVIEW_PERIOD_TRADES) == 0 and self.current_stats.total_trades > 0
    
    def get_review_recommendation(self) -> str:
        """Fornece recomendação de revisão do sistema"""
        checks = []
        
        exp_check = self.check_expectancy()
        if exp_check["alert"]:
            checks.append(f"Expectancy: {exp_check['alert']}")
        
        wr_check = self.check_win_rate()
        if wr_check["alert"]:
            checks.append(f"Win Rate: {wr_check['alert']}")
        
        rr_check = self.check_rr_ratio()
        if rr_check["alert"]:
            checks.append(f"RR: {rr_check['alert']}")
        
        regime = self.detect_regime_change()
        if regime:
            checks.append(regime)
        
        if checks:
            return "\n".join(checks)
        else:
            return "✓ Sistema operando dentro de parâmetros normais"
    
    def get_agent_status(self) -> str:
        """Retorna status do agente"""
        return (
            f"Agent: {self.agent_id} | "
            f"Trades: {self.current_stats.total_trades} | "
            f"WinRate: {self.current_stats.win_rate:.0%} | "
            f"Expectancy: {self.current_stats.expectancy:+.0%}"
        )
