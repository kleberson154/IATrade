"""
Connector Bybit API
Comunicação segura com Bybit Demo API
IMPORTANTE: Usa API demo, não testnet
"""

import logging
import requests
import hmac
import hashlib
import time
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
                 mode: str = BYBIT_API_MODE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.mode = mode.lower()
        
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{mode}")
        
        if self.mode not in self.ENDPOINTS:
            raise ValueError(f"Modo inválido: {mode}. Use: {list(self.ENDPOINTS.keys())}")
        
        self.base_url = self.ENDPOINTS[self.mode]
        self.logger.info(f"[OK] BybitConnector inicializado: {self.mode.upper()} mode")
        
        # Simulação para testes sem credenciais reais
        self.is_simulated = not (api_key and api_secret)
        if self.is_simulated:
            self.logger.warning("[SIMULADO] Modo SIMULADO (sem credenciais reais)")
        
        # Cache para dados simulados
        self._simulated_positions = {}
    
    def _generate_signature(self, params: str) -> str:
        """Gera assinatura HMAC para autenticação"""
        if self.is_simulated:
            return "simulated_signature"
        
        return hmac.new(
            self.api_secret.encode(),
            params.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: Dict = None, 
                data: Dict = None) -> Dict:
        """Faz requisição à API"""
        
        if self.is_simulated:
            self.logger.debug(f"[SIM] {method} {endpoint}")
            return {"ret_code": 0, "result": {}}
        
        try:
            url = f"{self.base_url}{endpoint}"
            headers = {
                "X-BYBIT-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }
            
            # Adiciona timestamp e assinatura
            timestamp = str(int(time.time() * 1000))
            
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=10)
            
            return response.json()
        
        except Exception as e:
            self.logger.error(f"Erro na requisição: {e}")
            return {"ret_code": -1, "ret_msg": str(e)}
    
    def get_account_info(self) -> Dict:
        """Retorna informações da conta"""
        if self.is_simulated:
            return {
                "wallet_balance": 100.0,
                "available_balance": 100.0,
                "used_margin": 0.0,
            }
        
        result = self._request("GET", "/v5/account/wallet-balance")
        return result.get("result", {})
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List[Dict]:
        """
        Busca candles (klines) históricos
        
        Args:
            symbol: BTCUSDT
            interval: 5m, 15m, 1h, etc
            limit: número de candles (máximo 200)
        
        Returns:
            Lista de candles com [open_time, open, high, low, close, volume]
        """
        if self.is_simulated:
            # Retorna dados simulados
            return self._get_simulated_klines(symbol, interval, limit)
        
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, 200),
        }
        
        result = self._request("GET", "/v5/market/kline", params=params)
        
        if result.get("ret_code") == 0:
            klines = result.get("result", {}).get("list", [])
            # Bybit retorna em formato: [time, open, high, low, close, volume, turnover]
            return klines
        
        return []
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Retorna preço atual"""
        if self.is_simulated:
            return 42500.0  # Preço simulado
        
        params = {
            "category": "linear",
            "symbol": symbol,
        }
        
        result = self._request("GET", "/v5/market/tickers", params=params)
        
        if result.get("ret_code") == 0:
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
        if self.is_simulated:
            order_id = f"SIM-{int(time.time() * 1000)}"
            self._simulated_positions[order_id] = {
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price or 42500.0,
                "status": "FILLED",
            }
            self.logger.info(f"[SIM] Order placed: {order_id}")
            return order_id
        
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
        
        if result.get("ret_code") == 0:
            return result.get("result", {}).get("orderId", "")
        
        raise Exception(f"Erro ao colocar ordem: {result.get('ret_msg')}")
    
    def set_stop_loss(self, symbol: str, order_id: str, stop_price: float) -> bool:
        """Define stop loss para uma ordem"""
        if self.is_simulated:
            self.logger.info(f"[SIM] Stop loss: {stop_price}")
            return True
        
        # Bybit usa ordem separada para stop
        data = {
            "category": "linear",
            "symbol": symbol,
            "orderId": order_id,
            "stopLoss": str(stop_price),
        }
        
        result = self._request("POST", "/v5/order/amend", data=data)
        return result.get("ret_code") == 0
    
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
        if self.is_simulated:
            self.logger.info(f"[SIM] Take profits: {tp_levels}")
            return True
        
        # Implementar lógica de TP múltiplos em Bybit
        # Bybit suporta TP via ordens, ou previsões
        
        return True  # Placeholder
    
    def close_position(self, symbol: str, trade_id: str) -> bool:
        """Fecha posição"""
        if self.is_simulated:
            self.logger.info(f"[SIM] Position closed: {trade_id}")
            if trade_id in self._simulated_positions:
                del self._simulated_positions[trade_id]
            return True
        
        data = {
            "category": "linear",
            "symbol": symbol,
            "orderId": trade_id,
        }
        
        result = self._request("POST", "/v5/order/cancel", data=data)
        return result.get("ret_code") == 0
    
    def get_open_positions(self) -> List[Dict]:
        """Retorna posições abertas"""
        if self.is_simulated:
            return list(self._simulated_positions.values())
        
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
        if self.is_simulated:
            # Retorna histórico simulado
            return self._get_simulated_closed_orders(symbol, limit)
        
        params = {
            "category": "linear",
            "orderStatus": "Cancelled,Filled,Rejected",  # Busca ordens finalizadas
            "limit": min(limit, 100),  # Máximo 100
        }
        
        if symbol:
            params["symbol"] = symbol
        
        result = self._request("GET", "/v5/order/history", params=params)
        
        if result.get("ret_code") == 0:
            orders = result.get("result", {}).get("list", [])
            self.logger.info(f"[OK] Carregado histórico: {len(orders)} ordens fechadas")
            return orders
        
        self.logger.warning(f"Erro ao buscar closed orders: {result.get('ret_msg')}")
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
        if self.is_simulated:
            # Retorna histórico simulado
            return self._get_simulated_trade_history(symbol, limit)
        
        params = {
            "category": "linear",
            "limit": min(limit, 100),  # Máximo 100
        }
        
        if symbol:
            params["symbol"] = symbol
        
        result = self._request("GET", "/v5/execution/list", params=params)
        
        if result.get("ret_code") == 0:
            executions = result.get("result", {}).get("list", [])
            self.logger.info(f"[OK] Carregado histórico: {len(executions)} execuções de trade")
            return executions
        
        self.logger.warning(f"Erro ao buscar trade history: {result.get('ret_msg')}")
        return []
    
    # ===== MÉTODOS DE SIMULAÇÃO =====
    
    def _get_simulated_klines(self, symbol: str, interval: str, limit: int) -> List:
        """Gera candles simulados para testes (com padrões que geram sinais)"""
        import random
        
        candles = []
        base_price = 42500.0
        current_time = int(time.time())
        
        # Gera padrão de MOMENTUM: 3+ candles em alta com closes acima das aberturas
        # Ou padrão de BREAKOUT: compressão seguida de rompimento
        
        pattern = random.choice(['momentum_up', 'momentum_down', 'breakout_up', 'breakout_down', 'mean_reversion'])
        
        # Fase 1: Compressão (ATR baixo)
        for i in range(15):
            move = random.uniform(-0.002, 0.002)  # ±0.2% - compressão
            
            open_price = base_price * (1 + move * 0.3)
            close_price = base_price * (1 + move * 0.2)
            high_price = max(open_price, close_price) * (1 + random.uniform(0.0001, 0.0003))
            low_price = min(open_price, close_price) * (1 - random.uniform(0.0001, 0.0003))
            volume = random.uniform(100, 300)
            
            base_price = close_price
            
            candle = [
                str(current_time - (limit - i) * 300),
                str(round(open_price, 2)),
                str(round(high_price, 2)),
                str(round(low_price, 2)),
                str(round(close_price, 2)),
                str(round(volume, 2)),
                str(round(volume * close_price, 2)),
            ]
            candles.append(candle)
        
        # Fase 2: Movimento de Trend/Breakout
        if pattern == 'momentum_up':
            # 3+ candles com close > open (bullish)
            for i in range(15, limit):
                move = random.uniform(0.003, 0.008)  # +0.3-0.8% tendência altista
                noise = random.uniform(-0.001, 0.001)
                
                open_price = base_price
                close_price = base_price * (1 + move + noise)
                high_price = close_price * (1 + random.uniform(0.001, 0.003))
                low_price = open_price * (1 - random.uniform(0.001, 0.003))
                volume = random.uniform(400, 800)
                
                base_price = close_price
                
                candle = [
                    str(current_time - (limit - i) * 300),
                    str(round(open_price, 2)),
                    str(round(high_price, 2)),
                    str(round(low_price, 2)),
                    str(round(close_price, 2)),
                    str(round(volume, 2)),
                    str(round(volume * close_price, 2)),
                ]
                candles.append(candle)
                
        elif pattern == 'momentum_down':
            # 3+ candles com close < open (bearish)
            for i in range(15, limit):
                move = random.uniform(-0.008, -0.003)  # -0.8-0.3% tendência baixista
                noise = random.uniform(-0.001, 0.001)
                
                open_price = base_price
                close_price = base_price * (1 + move + noise)
                low_price = close_price * (1 - random.uniform(0.001, 0.003))
                high_price = open_price * (1 + random.uniform(0.001, 0.003))
                volume = random.uniform(400, 800)
                
                base_price = close_price
                
                candle = [
                    str(current_time - (limit - i) * 300),
                    str(round(open_price, 2)),
                    str(round(high_price, 2)),
                    str(round(low_price, 2)),
                    str(round(close_price, 2)),
                    str(round(volume, 2)),
                    str(round(volume * close_price, 2)),
                ]
                candles.append(candle)
        
        elif pattern == 'breakout_up':
            # Rompimento para cima
            for i in range(15, limit):
                move = random.uniform(0.004, 0.012)  # +0.4-1.2% breakout
                
                open_price = base_price
                close_price = base_price * (1 + move)
                high_price = close_price * (1 + random.uniform(0.002, 0.005))
                low_price = open_price * (1 - random.uniform(0.001, 0.002))
                volume = random.uniform(600, 1200)
                
                base_price = close_price
                
                candle = [
                    str(current_time - (limit - i) * 300),
                    str(round(open_price, 2)),
                    str(round(high_price, 2)),
                    str(round(low_price, 2)),
                    str(round(close_price, 2)),
                    str(round(volume, 2)),
                    str(round(volume * close_price, 2)),
                ]
                candles.append(candle)
                
        elif pattern == 'breakout_down':
            # Rompimento para baixo
            for i in range(15, limit):
                move = random.uniform(-0.012, -0.004)  # -1.2-0.4% breakout
                
                open_price = base_price
                close_price = base_price * (1 + move)
                low_price = close_price * (1 - random.uniform(0.002, 0.005))
                high_price = open_price * (1 + random.uniform(0.001, 0.002))
                volume = random.uniform(600, 1200)
                
                base_price = close_price
                
                candle = [
                    str(current_time - (limit - i) * 300),
                    str(round(open_price, 2)),
                    str(round(high_price, 2)),
                    str(round(low_price, 2)),
                    str(round(close_price, 2)),
                    str(round(volume, 2)),
                    str(round(volume * close_price, 2)),
                ]
                candles.append(candle)
        
        else:  # mean_reversion
            # Oscilação em range
            for i in range(15, limit):
                move = random.uniform(-0.005, 0.005)  # ±0.5% oscilação
                
                open_price = base_price * (1 + move * 0.4)
                close_price = base_price * (1 - move * 0.3)
                high_price = max(open_price, close_price) * (1 + random.uniform(0.001, 0.003))
                low_price = min(open_price, close_price) * (1 - random.uniform(0.001, 0.003))
                volume = random.uniform(200, 500)
                
                base_price = close_price
                
                candle = [
                    str(current_time - (limit - i) * 300),
                    str(round(open_price, 2)),
                    str(round(high_price, 2)),
                    str(round(low_price, 2)),
                    str(round(close_price, 2)),
                    str(round(volume, 2)),
                    str(round(volume * close_price, 2)),
                ]
                candles.append(candle)
        
        self.logger.debug(f"[SIM] Gerou padrão {pattern} com {len(candles)} candles")
        return candles
    
    def _get_simulated_closed_orders(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Gera histórico simulado de ordens fechadas"""
        import random
        
        closed_orders = []
        current_time = int(time.time())
        symbols = [symbol] if symbol else ["BTCUSDT", "ETHUSDT", "LINKUSDT"]
        
        # Simula 10-30 ordens fechadas, mas não ultrapassa o limit
        max_orders = min(30, limit)
        min_orders = min(10, limit)
        num_orders = random.randint(min_orders, max_orders)
        
        for i in range(num_orders):
            order_id = f"SIM-ORDER-{current_time - i * 3600}-{random.randint(1000, 9999)}"
            order_symbol = random.choice(symbols)
            side = random.choice(["Buy", "Sell"])
            
            order_price = 42500.0 if "BTC" in order_symbol else (random.uniform(2000, 3500) if "ETH" in order_symbol else random.uniform(10, 50))
            order_qty = random.uniform(0.01, 1.0)
            cum_exec_qty = order_qty  # Totalmente executada
            status = "Filled"  # Simulamos como preenchidas
            
            created_time = str((current_time - i * 3600) * 1000)  # em millisegundos
            updated_time = str((current_time - i * 3600 + random.randint(1, 300)) * 1000)
            
            order = {
                "orderId": order_id,
                "orderLinkId": "",
                "symbol": order_symbol,
                "side": side,
                "orderPrice": str(round(order_price, 2)),
                "orderQty": str(round(order_qty, 4)),
                "cumExecQty": str(round(cum_exec_qty, 4)),
                "cumExecValue": str(round(order_price * cum_exec_qty, 2)),
                "avgPrice": str(round(order_price, 2)),
                "status": status,
                "timeInForce": "IOC",
                "orderType": "Market",
                "createdTime": created_time,
                "updatedTime": updated_time,
                "cancelType": "",
            }
            
            closed_orders.append(order)
        
        self.logger.debug(f"[SIM] Retornando {len(closed_orders)} closed orders")
        return closed_orders
    
    def _get_simulated_trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Gera histórico simulado de execução de trades (fills)"""
        import random
        
        trade_history = []
        current_time = int(time.time())
        symbols = [symbol] if symbol else ["BTCUSDT", "ETHUSDT", "LINKUSDT"]
        
        # Simula 15-40 execuções de trades, mas não ultrapassa o limit
        max_trades = min(40, limit)
        min_trades = min(15, limit)
        num_trades = random.randint(min_trades, max_trades)
        
        for i in range(num_trades):
            exec_id = f"SIM-EXEC-{current_time - i * 1800}-{random.randint(100000, 999999)}"
            order_id = f"SIM-ORDER-{current_time - i * 3600}-{random.randint(1000, 9999)}"
            trade_symbol = random.choice(symbols)
            side = random.choice(["Buy", "Sell"])
            
            # Preço com variação realista
            base_price = 42500.0 if "BTC" in trade_symbol else (random.uniform(2000, 3500) if "ETH" in trade_symbol else random.uniform(10, 50))
            exec_price = base_price * (1 + random.uniform(-0.01, 0.01))  # ±1% variação
            exec_qty = random.uniform(0.001, 0.5)
            
            exec_time = str((current_time - i * 1800) * 1000)  # em millisegundos
            
            # Taxa de fee simulada (0.075% para maker, 0.1% para taker em demo)
            fee_rate = random.choice([0.00075, 0.001])
            trading_fee = exec_price * exec_qty * fee_rate
            
            exec_type = random.choice(["Trade", "BustTrade"])
            
            trade = {
                "execId": exec_id,
                "orderId": order_id,
                "orderLinkId": "",
                "symbol": trade_symbol,
                "side": side,
                "execPrice": str(round(exec_price, 2)),
                "execQty": str(round(exec_qty, 4)),
                "execValue": str(round(exec_price * exec_qty, 2)),
                "isMaker": random.choice([True, False]),
                "feeRate": str(fee_rate),
                "tradingFee": str(round(trading_fee, 4)),
                "execTime": exec_time,
                "execType": exec_type,
                "execFee": str(round(trading_fee, 4)),
            }
            
            trade_history.append(trade)
        
        self.logger.debug(f"[SIM] Retornando {len(trade_history)} trades executados")
        return trade_history
