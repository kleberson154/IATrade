"""
Connector Bybit API
Comunicação segura com Bybit Demo API
IMPORTANTE: Usa API demo, não testnet
"""

import logging
import os
import json
import requests
import hmac
import hashlib
import time
from urllib.parse import urlencode
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from config.settings import BYBIT_API_KEY, BYBIT_API_SECRET, BYBIT_API_MODE


class BybitConnector:
    """
    Connector para Bybit API
    Suporta: Demo, Testnet, Real (baseado em BYBIT_API_MODE)
    """
    
    # Endpoints
    ENDPOINTS = {
        "demo": "https://api-demo.bybit.com",
        "testnet": "https://api-testnet.bybit.com",
        "real": "https://api.bybit.com",
    }
    
    def __init__(self, api_key: str = BYBIT_API_KEY, 
                 api_secret: str = BYBIT_API_SECRET,
                 mode: str = None):
        api_key = api_key or os.getenv("BYBIT_API_KEY", BYBIT_API_KEY)
        api_secret = api_secret or os.getenv("BYBIT_API_SECRET", BYBIT_API_SECRET)
        mode = (mode or os.getenv("BYBIT_API_MODE", os.getenv("BYBIT_MODE", BYBIT_API_MODE))).lower()

        self.api_key = api_key
        self.api_secret = api_secret
        self.mode = mode
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{mode}")
        
        if self.mode not in self.ENDPOINTS:
            raise ValueError(f"Modo inválido: {mode}. Use: {list(self.ENDPOINTS.keys())}")
        
        self.base_url = self.ENDPOINTS[self.mode]
        self.logger.info(f"[OK] BybitConnector inicializado: {self.mode.upper()} mode")
        

    
    def _generate_signature(self, params: str) -> str:
        """Gera assinatura HMAC para autenticação"""
        return hmac.new(
            self.api_secret.encode(),
            params.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _build_query_string(self, params: Dict) -> str:
        if not params:
            return ""

        sorted_items = sorted((k, v) for k, v in params.items() if v is not None)
        return urlencode(sorted_items, safe=":")

    def _request(self, method: str, endpoint: str, params: Dict = None, 
                data: Dict = None) -> Dict:
        """Faz requisição à API"""
        
        try:
            url = f"{self.base_url}{endpoint}"
            timestamp = str(int(time.time() * 1000))
            recv_window = "5000"

            body = json.dumps(data, separators=(",", ":"), sort_keys=True) if data else ""
            query_string = self._build_query_string(params)
            sign_payload = f"{timestamp}{method.upper()}{endpoint}{query_string}{body}"
            signature = hmac.new(
                self.api_secret.encode(),
                sign_payload.encode(),
                hashlib.sha256
            ).hexdigest()

            headers = {
                "X-BAPI-API-KEY": self.api_key,
                "X-BAPI-SIGN": signature,
                "X-BAPI-TIMESTAMP": timestamp,
                "X-BAPI-RECV-WINDOW": recv_window,
                "Content-Type": "application/json",
            }
            
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            return response.json()
        
        except Exception as e:
            self.logger.error(f"Erro na requisição: {e}")
            return {"retCode": -1, "retMsg": str(e)}
    
    def get_account_info(self) -> Dict:
        """Retorna informações da conta"""
        result = self._request("GET", "/v5/account/wallet-balance")
        account = result.get("result", {})
        return account
    
    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> List[Dict]:
        """
        Busca candles (klines) históricos
        
        Args:
            symbol: BTCUSDT
            interval: 5m, 15m, 1h, etc
            limit: número de candles (máximo 200)
        
        Returns:
            Lista de candles com [open_time, open, high, low, close, volume]
        """
        # Normaliza o intervalo para o formato Bybit V5
        interval_map = {
            "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
            "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
            "1d": "D", "1w": "W", "1M": "M"
        }
        interval = interval_map.get(interval, interval)
        
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 200),
        }
        
        result = self._request("GET", "/v5/market/kline", params=params)
        print(f"get_klines: {result}")
        
        if result.get("retCode") == 0:
            klines = result.get("result", {}).get("list", [])
            print(f"get_klines - klines: {klines}")
            # Bybit retorna em formato: [time, open, high, low, close, volume, turnover]
            return klines
        
        return []
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Retorna preço atual"""
        params = {
            "category": "linear",
            "symbol": symbol,
        }
        
        result = self._request("GET", "/v5/market/tickers", params=params)
        
        if result.get("retCode") == 0:
            tickers = result.get("result", {}).get("list", [])
            if tickers:
                return float(tickers[0].get("lastPrice", 0))
        
        return None
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float, price: float = None,
                   timeout_seconds: int = 30) -> str:
        """
        Coloca ordem
        
        Args:
            symbol: BTCUSDT
            side: BUY ou SELL
            order_type: MARKET ou LIMIT
            quantity: quantidade em BTC
            price: preço (obrigatório para LIMIT)
        
        Returns:
            order_id
        """
        data = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(quantity),
            "timeInForce": "IOC",  # Imediato ou cancelado
        }
        
        if order_type == "LIMIT" and price:
            data["price"] = str(price)
        
        result = self._request("POST", "/v5/order/create", data=data)
        
        if result.get("retCode") == 0:
            return result.get("result", {}).get("orderId", "")
        
        raise Exception(f"Erro ao colocar ordem: {result.get('retMsg')}")
    
    def set_stop_loss(self, symbol: str, order_id: str, stop_price: float) -> bool:
        """Define stop loss para uma ordem"""
        # Bybit usa ordem separada para stop
        data = {
            "category": "linear",
            "symbol": symbol,
            "orderId": order_id,
            "stopLoss": str(stop_price),
        }
        
        result = self._request("POST", "/v5/order/amend", data=data)
        return result.get("retCode") == 0
    
    def set_take_profits(self, symbol: str, order_id: str, 
                        tp_levels: Dict) -> bool:
        """
        Define múltiplos take profits
        
        Args:
            tp_levels: {
                "tp1": {"price": float, "percent": int},
                "tp2": {"price": float, "percent": int},
                "tp3": {"price": float, "percent": int},
            }
        """
        # Implementar lógica de TP múltiplos em Bybit
        # Bybit suporta TP via ordens, ou previsões
        
        return True  # Placeholder
    
    def close_position(self, symbol: str, trade_id: str) -> bool:
        """Fecha posição"""
        data = {
            "category": "linear",
            "symbol": symbol,
            "orderId": trade_id,
        }
        
        result = self._request("POST", "/v5/order/cancel", data=data)
        return result.get("retCode") == 0
    
    def get_open_positions(self) -> List[Dict]:
        """Retorna posições abertas"""
        params = {
            "category": "linear",
        }
        
        result = self._request("GET", "/v5/position/list", params=params)
        return result.get("result", {}).get("list", [])
    
    def get_closed_orders(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """
        Retorna histórico de ordens fechadas (trades executadas)
        
        Args:
            symbol: BTCUSDT (opcional, busca todos se não informado)
            limit: número máximo de ordens (padrão 50)
        
        Returns:
            Lista de ordens fechadas com [orderId, symbol, side, orderPrice, orderQty, cumExecQty, status, createdTime, updatedTime]
        """
        params = {
            "category": "linear",
            "orderStatus": "Cancelled,Filled,Rejected",  # Busca ordens finalizadas
            "limit": min(limit, 100),  # Máximo 100
        }
        
        if symbol:
            params["symbol"] = symbol
        
        result = self._request("GET", "/v5/order/history", params=params)
        
        if result.get("retCode") == 0:
            orders = result.get("result", {}).get("list", [])
            self.logger.info(f"[OK] Carregado histórico: {len(orders)} ordens fechadas")
            return orders
        
        self.logger.warning(f"Erro ao buscar closed orders: {result.get('retMsg')}")
        return []
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """
        Retorna histórico de execução de trades (fills/executions)
        
        Args:
            symbol: BTCUSDT (opcional)
            limit: número máximo (padrão 50)
        
        Returns:
            Lista de execuções com [execId, orderId, symbol, side, execPrice, execQty, execTime, feeRate, tradingFee, execType]
        """
        params = {
            "category": "linear",
            "limit": min(limit, 100),  # Máximo 100
        }
        
        if symbol:
            params["symbol"] = symbol
        
        result = self._request("GET", "/v5/execution/list", params=params)
        
        if result.get("retCode") == 0:
            executions = result.get("result", {}).get("list", [])
            self.logger.info(f"[OK] Carregado histórico: {len(executions)} execuções de trade")
            return executions
        
        self.logger.warning(f"Erro ao buscar trade history: {result.get('retMsg')}")
        return []
    
