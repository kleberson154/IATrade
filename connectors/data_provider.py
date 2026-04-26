"""
DataProvider - Interface abstrata para múltiplas fontes de dados
Permite usar dados simulados, históricos, ou real-time sem alterar o bot
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
import pandas as pd
import json

@dataclass
class CandleData:
    """Representa uma vela OHLCV com tipagem forte"""
    timestamp: int  # Unix timestamp em ms
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def time_str(self) -> str:
        """Retorna timestamp formatado"""
        return datetime.fromtimestamp(self.timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

class DataProvider(ABC):
    """Interface abstrata para provedores de dados"""
    
    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[CandleData]:
        """
        Obtém candles históricos
        
        Args:
            symbol: Ex: 'BTCUSDT'
            interval: Ex: '5', '15', '1h'
            limit: Número de candles
            start_time: Timestamp em ms (opcional)
            end_time: Timestamp em ms (opcional)
        
        Returns:
            Lista de CandleData ordenada por tempo
        """
        pass
    
    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """Retorna o preço mais recente"""
        pass
    
    @abstractmethod
    def get_candles_for_period(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[CandleData]:
        """Retorna candles para um período específico"""
        pass

class BybitDataProvider(DataProvider):
    """Busca dados reais diretamente da Bybit para Backtest ou Real-time"""
    
    def __init__(self, connector):
        self.connector = connector # Sua instância do BybitConnector

    def get_klines(self, symbol: str, interval: str, limit: int = 100, 
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[CandleData]:
        # A Bybit usa strings para intervalos (ex: '5', '15', '60', 'D')
        # Se o seu backtester passa inteiros, convertemos aqui
        interval_str = str(interval)
        
        # Chama o método que já existe no seu BybitConnector
        raw_klines = self.connector.get_klines(
            symbol=symbol, 
            interval=interval_str, 
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )
        
        if not raw_klines:
            return []

        return [CandleData(
            timestamp=int(k[0]),
            open=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5])
        ) for k in raw_klines]

    def get_candles_for_period(self, symbol: str, interval: str, 
                               start_date: datetime, end_date: datetime) -> List[CandleData]:
        """Busca dados de longo prazo (ex: 90 dias) fazendo paginação na API"""
        all_candles = []
        current_start = int(start_date.timestamp() * 1000)
        final_end = int(end_date.timestamp() * 1000)
        
        print(f"⏳ Coletando dados históricos de {symbol}...")

        while current_start < final_end:
            # Busca lotes de 1000 (máximo da Bybit)
            batch = self.get_klines(symbol, interval, limit=1000, start_time=current_start)
            
            if not batch:
                break
                
            all_candles.extend(batch)
            
            # O novo início é o timestamp do último candle recebido + 1ms
            new_start = batch[-1].timestamp + 1
            
            # Segurança para não entrar em loop infinito se a API parar de responder
            if new_start <= current_start:
                break
                
            current_start = new_start
            
            # Pequeno pause para não tomar ban por excesso de requisições (Rate Limit)
            time.sleep(0.1)
            
            if len(all_candles) % 5000 == 0:
                print(f"  > {len(all_candles)} candles processados...")

        # Filtra para garantir que não passamos da data final
        return [c for c in all_candles if c.timestamp <= final_end]

    def get_latest_price(self, symbol: str) -> float:
        # Reutiliza o método de klines para pegar o último preço
        candles = self.get_klines(symbol, "1", limit=1)
        return candles[0].close if candles else 0.0
