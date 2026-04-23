"""
Agente de Análise de Mercado
Detecta setups, monitora volatilidade, análise multi-timeframe
"""

import logging
from typing import Optional, List, Dict
from models.trade_models import SetupSignal, VolatilityData
from core.setup_detector import SetupDetector, SetupValidator
from core.volatility import VolatilityCalculator, VolatilityAnalyzer


class MarketAnalysisAgent:
    """
    Agente responsável por:
    - Detectar setups de trading
    - Analisar volatilidade
    - Análise multi-timeframe
    - Fornecer sinais de oportunidade
    """
    
    def __init__(self, agent_id: str = "MA-001"):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{agent_id}")
        
        self.setup_detector = SetupDetector()
        self.setup_validator = SetupValidator()
        
        self.volatility_calc = VolatilityCalculator()
        self.volatility_analyzer = VolatilityAnalyzer()
        
        # Cache de análise
        self.last_signal: Optional[SetupSignal] = None
        self.analysis_history: List[Dict] = []
    
    def analyze_candle_data(self, candles_data: Dict[str, List]) -> Dict:
        """
        Analisa dados de candles e retorna análise completa
        
        Args:
            candles_data: {
                "closes": [...],
                "highs": [...],
                "lows": [...],
                "volumes": [...],
                "current_price": float,
            }
        """
        analysis = {
            "timestamp": None,
            "market_analysis": {},
            "volatility_analysis": {},
            "setup_signals": [],
            "best_signal": None,
            "recommendation": None,
        }
        
        closes = candles_data.get("closes", [])
        highs = candles_data.get("highs", [])
        lows = candles_data.get("lows", [])
        volumes = candles_data.get("volumes", [])
        current_price = candles_data.get("current_price", 0)
        
        if not all([closes, highs, lows, current_price]):
            self.logger.error("Dados incompletos para análise")
            return analysis
        
        # 1. Detecta setups
        signals = self.setup_detector.detect_all_setups(
            closes, highs, lows, current_price
        )
        
        analysis["setup_signals"] = signals
        
        if signals:
            best_signal = signals[0]  # Já está ordenado por confiança
            analysis["best_signal"] = best_signal
            self.last_signal = best_signal
            
            is_valid, score, msg = self.setup_validator.validate_setup_signal(best_signal)
            analysis["market_analysis"]["best_setup_valid"] = is_valid
            analysis["market_analysis"]["best_setup_score"] = score
            analysis["market_analysis"]["best_setup_reason"] = msg
        
        # 2. Análise de volatilidade
        vol_data = self.volatility_calc.get_volatility_data(
            "BTCUSDT", "5m", current_price, highs, lows, closes
        )
        
        if vol_data:
            self.volatility_analyzer.add_volatility(vol_data.atr_percent)
            
            analysis["volatility_analysis"] = {
                "atr_value": vol_data.atr_value,
                "atr_percent": vol_data.atr_percent,
                "regime": self.volatility_calc.get_volatility_regime(vol_data.atr_percent),
                "high_volatility": vol_data.high_volatility,
                "low_volatility": vol_data.low_volatility,
                "avg_volatility": self.volatility_analyzer.get_average_volatility(),
                "vol_expanding": self.volatility_analyzer.is_volatility_expanding(),
                "vol_percentile": self.volatility_analyzer.get_volatility_percentile(vol_data.atr_percent),
            }
        
        # 3. Recomendação
        if signals and analysis["market_analysis"].get("best_setup_valid"):
            analysis["recommendation"] = {
                "action": "CONSIDER_TRADE",
                "signal": signals[0],
                "volatility": analysis["volatility_analysis"].get("regime", "UNKNOWN"),
            }
        else:
            analysis["recommendation"] = {
                "action": "WAIT",
                "reason": "Nenhum sinal válido encontrado",
            }
        
        # Store na história
        self.analysis_history.append(analysis)
        if len(self.analysis_history) > 100:
            self.analysis_history = self.analysis_history[-100:]
        
        return analysis
    
    def get_multi_timeframe_confirmation(self, analysis_dict: Dict[str, Dict]) -> Dict:
        """
        Valida sinal em múltiplos timeframes
        
        Args:
            analysis_dict: {
                "5m": {...análise 5m...},
                "15m": {...análise 15m...},
                "1h": {...análise 1h...},
            }
        """
        confirmation = {
            "timeframes_analysed": list(analysis_dict.keys()),
            "direction_alignment": None,
            "confidence_score": 0.0,
            "recommendation": "WAIT",
            "details": {},
        }
        
        directions = []
        confidence_scores = []
        
        for tf, analysis in analysis_dict.items():
            if analysis.get("best_signal"):
                signal = analysis["best_signal"]
                directions.append(signal.direction.value)
                score = analysis["market_analysis"].get("best_setup_score", 0)
                confidence_scores.append(score)
                
                confirmation["details"][tf] = {
                    "direction": signal.direction.value,
                    "setup": signal.setup_type,
                    "confidence": signal.confidence,
                    "score": score,
                }
        
        # Verifica alinhamento
        if directions:
            alignment = len(set(directions)) == 1  # Todos na mesma direção?
            confirmation["direction_alignment"] = alignment
            confirmation["confidence_score"] = sum(confidence_scores) / len(confidence_scores) / 100
            
            if alignment and confirmation["confidence_score"] > 0.55:
                confirmation["recommendation"] = "STRONG_SETUP"
            elif alignment:
                confirmation["recommendation"] = "SETUP_CONFIRMED"
            else:
                confirmation["recommendation"] = "CONFLICTING_SIGNALS"
        
        return confirmation
    
    def get_trading_hours_status(self) -> Dict:
        """
        Retorna status de horário de trading
        Para demo: sempre aberto, mas registra padrões
        """
        return {
            "market_open": True,
            "trading_allowed": True,
            "note": "Demo - sempre aberto",
        }
    
    def get_agent_status(self) -> str:
        """Retorna status do agente"""
        status = f"Agent: {self.agent_id} | "
        status += f"Sinais detectados: {len(self.analysis_history)} | "
        
        if self.last_signal:
            status += f"Último sinal: {self.last_signal.setup_type} {self.last_signal.direction.value.upper()}"
        else:
            status += "Sem sinais recentes"
        
        return status
