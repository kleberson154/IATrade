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
    
    def _build_query_string(self, params: Dict) -> str:
        if not params:
            return ""

        sorted_items = sorted((k, v) for k, v in params.items() if v is not None)
        return urlencode(sorted_items, safe=":")

    def _generate_signature(self, timestamp: str, payload: str) -> str:
        recv_window = "5000"
        param_str = timestamp + self.api_key + recv_window + payload
        
        return hmac.new(
            self.api_secret.encode("utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        method = method.upper()
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        if method == "GET":
            payload = urlencode(params) if params else ""
            full_url = f"{self.base_url}{endpoint}"
            if payload:
                full_url += f"?{payload}"
        else:
            payload = json.dumps(params) if params else ""
            full_url = f"{self.base_url}{endpoint}"

        signature = self._generate_signature(timestamp, payload)

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                response = requests.get(full_url, headers=headers, timeout=10)
            else:
                response = requests.post(full_url, headers=headers, data=payload, timeout=10)
            if response.status_code != 200:
                self.logger.error(f"Erro Bybit {response.status_code}: {response.text}")

            return response.json()
            
        except Exception as e:
            self.logger.error(f"Erro na requisição {method} {endpoint}: {str(e)}")
            return {"retCode": -1, "retMsg": str(e)}
    
    def get_account_info(self) -> Dict:
        """Retorna informações da conta"""
        result = self._request("GET", "/v5/account/wallet-balance")
        account = result.get("result", {})
        return account
    
    def get_klines(self, symbol: str, interval: str, limit: int = 200, 
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> List[List]:
        """
        Busca candles (klines) históricos com suporte a períodos específicos
        """
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
            "limit": limit, # Removi o min(limit, 200) para aceitar até 1000 se necessário
        }
        
        # Adiciona filtros de tempo se fornecidos
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        
        result = self._request("GET", "/v5/market/kline", params=params)
        
        if result.get("retCode") == 0:
            klines = result.get("result", {}).get("list", [])
            # A Bybit retorna do mais novo para o mais antigo. 
            # Para backtest, geralmente revertemos para ordem cronológica.
            return klines[::-1] 
        
        self.logger.error(f"Erro ao buscar klines: {result.get('retMsg')}")
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
        
        data = {
            "category": "linear",
            "symbol": symbol,
            "side": side,
            "orderType": order_type,
            "qty": str(quantity),
            "timeInForce": "IOC",
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
    
    def set_trading_stop(self, symbol: str, stop_loss: float, side: str):
        """
        Atualiza o Stop Loss de uma posição ativa na Bybit V5.
        """
        try:
            payload = {
                "category": "linear",
                "symbol": symbol,
                "stopLoss": str(stop_loss),
                "slTriggerBy": "LastPrice",
                "tpslMode": "Full",
                "positionIdx": 0 # 0 para unidirecional, 1 para Hedge (Buy), 2 para Hedge (Sell)
            }
            
            # O endpoint da V5 para modificar posições
            endpoint = "/v5/position/trading-stop"
            
            # Aqui você usaria a lógica interna do seu conector para assinar e enviar
            response = self._request("POST", endpoint, data=payload)
            
            if response and response.get("retCode") == 0:
                self.logger.info(f"✅ SL atualizado na Bybit para {symbol}: {stop_loss}")
                return True
            else:
                error_msg = response.get("retMsg") if response else "Sem resposta"
                self.logger.error(f"❌ Erro ao atualizar SL na Bybit: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Falha na comunicação com Bybit para Trading Stop: {e}")
            return False
    
    def set_take_profits(self, symbol: str, side: str, total_qty: float, 
                          tp_levels: List) -> bool:
        """
        Cria ordens LIMIT individuais para cada nível de Take Profit.
        Args:
            symbol: Ex: "BTCUSDT"
            side: "Buy" (se você abriu um Long) ou "Sell" (se abriu um Short)
            total_qty: Quantidade total da posição aberta
            tp_levels: Lista de objetos TakeProfitLevel (do seu calculator)
        """
        # Se você comprou (Buy), o TP deve ser uma ordem de venda (Sell)
        exit_side = "Sell" if side == "Buy" else "Buy"
        
        success_count = 0
        
        for tp in tp_levels:
            # Calcula a quantidade exata para este nível de TP
            tp_qty = total_qty * tp.volume_percent
            
            # Formata para string respeitando a precisão (Bybit rejeita se houver muitos decimais)
            # Dica: use round(tp_qty, 3) ou conforme o símbolo
            
            data = {
                "category": "linear",
                "symbol": symbol,
                "side": exit_side,
                "orderType": "LIMIT",
                "qty": str(tp_qty),
                "price": str(round(tp.price, 2)),
                "timeInForce": "GTC", # Good Till Cancelled
                "reduceOnly": True,    # CRÍTICO: Garante que a ordem apenas fecha posição
                "positionIdx": 0       # 0 para modo unidirecional
            }
            
            result = self._request("POST", "/v5/order/create", data=data)
            
            if result.get("retCode") == 0:
                self.logger.info(f"✅ Ordem de {tp.label} enviada: {tp.price} (Qtd: {tp_qty})")
                success_count += 1
            else:
                self.logger.error(f"❌ Erro ao enviar {tp.label}: {result.get('retMsg')}")
        
        return success_count == len(tp_levels)
    
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
            return executions
        
        self.logger.warning(f"Erro ao buscar trade history: {result.get('retMsg')}")
        return []
    
