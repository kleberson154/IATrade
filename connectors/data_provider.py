"""
DataProvider - Interface abstrata para múltiplas fontes de dados
Permite usar dados simulados, históricos, ou real-time sem alterar o bot
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
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

class HistoricalDataProvider(DataProvider):
    """Fornece dados históricos de um arquivo CSV/JSON"""
    
    def __init__(self, data_file: str):
        """
        Args:
            data_file: Caminho do arquivo com dados históricos
        """
        self.data_file = data_file
        self.candles: Dict[str, Dict[str, List[CandleData]]] = {}
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do arquivo"""
        try:
            if self.data_file.endswith('.csv'):
                df = pd.read_csv(self.data_file)
            elif self.data_file.endswith('.json'):
                with open(self.data_file) as f:
                    data = json.load(f)
                df = pd.DataFrame(data)
            else:
                raise ValueError(f"Formato não suportado: {self.data_file}")
            
            # Converter para CandleData
            for _, row in df.iterrows():
                candle = CandleData(
                    timestamp=int(row['timestamp']),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume'])
                )
                
                # Agrupar por símbolo e intervalo (se houver)
                symbol = row.get('symbol', 'BTCUSDT')
                interval = row.get('interval', '5')
                
                if symbol not in self.candles:
                    self.candles[symbol] = {}
                if interval not in self.candles[symbol]:
                    self.candles[symbol][interval] = []
                
                self.candles[symbol][interval].append(candle)
            
            # Ordenar por timestamp
            for symbol in self.candles:
                for interval in self.candles[symbol]:
                    self.candles[symbol][interval].sort(key=lambda c: c.timestamp)
            
            print(f"[OK] Carregados {sum(len(self.candles[s][i]) for s in self.candles for i in self.candles[s])} candles")
        except Exception as e:
            print(f"[ERRO] Falha ao carregar dados: {e}")
            self.candles = {}
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[CandleData]:
        """Retorna candles históricos"""
        if symbol not in self.candles or interval not in self.candles[symbol]:
            return []
        
        candles = self.candles[symbol][interval]
        
        # Filtrar por tempo se especificado
        if start_time:
            candles = [c for c in candles if c.timestamp >= start_time]
        if end_time:
            candles = [c for c in candles if c.timestamp <= end_time]
        
        # Retornar últimos N
        return candles[-limit:] if limit else candles
    
    def get_latest_price(self, symbol: str) -> float:
        """Retorna o preço de fechamento mais recente"""
        if symbol not in self.candles:
            return 0.0
        
        # Pegar o intervalo com mais dados
        interval = list(self.candles[symbol].keys())[0]
        candles = self.candles[symbol][interval]
        
        if candles:
            return candles[-1].close
        return 0.0
    
    def get_candles_for_period(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[CandleData]:
        """Retorna candles para um período específico"""
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        
        return self.get_klines(symbol, interval, start_time=start_ms, end_time=end_ms)

class SimulatedDataProvider(DataProvider):
    """Fornece dados simulados/aleatórios para testes"""
    
    def __init__(
        self,
        starting_price: float = 42500,
        volatility: float = 0.02,
        trend_probability: float = 0.55
    ):
        self.starting_price = starting_price
        self.volatility = volatility
        self.trend_probability = trend_probability
    
    def _generate_random_candle(self, prev_close: float) -> CandleData:
        """Gera uma vela aleatória"""
        import random
        
        # Movimento aleatório
        trend = random.random() < self.trend_probability
        direction = 1 if trend else -1
        movement_percent = random.uniform(0, self.volatility) * direction
        
        close = prev_close * (1 + movement_percent)
        open_price = prev_close + random.uniform(-prev_close * 0.005, prev_close * 0.005)
        
        high = max(open_price, close) + random.uniform(0, prev_close * 0.005)
        low = min(open_price, close) - random.uniform(0, prev_close * 0.005)
        volume = random.uniform(100, 300)
        
        return CandleData(
            timestamp=int((datetime.now().timestamp() + random.random()) * 1000),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=volume
        )
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 100,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[CandleData]:
        """Gera candles simulados"""
        import random
        
        candles = []
        current_price = self.starting_price
        
        for _ in range(limit):
            candle = self._generate_random_candle(current_price)
            candles.append(candle)
            current_price = candle.close
        
        return candles
    
    def get_latest_price(self, symbol: str) -> float:
        """Retorna um preço simulado"""
        import random
        deviation = random.uniform(-self.starting_price * 0.05, self.starting_price * 0.05)
        return self.starting_price + deviation
    
    def get_candles_for_period(
        self,
        symbol: str,
        interval: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[CandleData]:
        """Retorna candles simulados para um período"""
        num_periods = (end_date - start_date).days * 288  # 5 candles de 5min por hora
        return self.get_klines(symbol, interval, limit=num_periods)
