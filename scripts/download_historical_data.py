#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
download_historical_data.py - Baixa dados históricos reais do Bitcoin via Bybit API
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import csv

class BybitHistoricalDownloader:
    """Baixa dados históricos do Bybit"""
    
    BASE_URL = "https://api.bybit.com"
    
    def __init__(self):
        self.session = None
        self.data = []
    
    async def download_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "5",
        days: int = 90,
        category: str = "spot"
    ):
        """
        Baixa candles históricos
        
        Args:
            symbol: Ex: BTCUSDT
            interval: Ex: 5, 15, 60, D (minutos ou D para dia)
            days: Quantos dias para trás
            category: spot ou linear
        """
        print(f"\n[DOWNLOAD] Iniciando download de {symbol} {interval}min (últimos {days} dias)")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Calcular datas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Para interval pequenos (5, 15 min), usar 200 candles por requisição
            # Bybit tem limite de 1000 candles por requisição
            candles_per_request = 200
            
            current_time = int(start_date.timestamp() * 1000)
            end_time = int(end_date.timestamp() * 1000)
            
            request_count = 0
            
            while current_time < end_time:
                try:
                    request_count += 1
                    
                    # Construir parâmetros
                    params = {
                        'category': category,
                        'symbol': symbol,
                        'interval': interval,
                        'start': current_time,
                        'limit': candles_per_request
                    }
                    
                    url = f"{self.BASE_URL}/v5/market/kline"
                    
                    print(f"[REQ {request_count}] Obtendo candles a partir de {datetime.fromtimestamp(current_time/1000).strftime('%Y-%m-%d %H:%M')}", end=" ... ")
                    
                    async with session.get(url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            if data.get('retCode') == 0 and data.get('result', {}).get('list'):
                                candles = data['result']['list']
                                
                                # Bybit retorna em ordem invertida (mais recentes primeiro)
                                for candle in reversed(candles):
                                    # Pode vir com 6 ou 7 elementos dependendo da versão da API
                                    ts = candle[0]
                                    o = candle[1]
                                    h = candle[2]
                                    l = candle[3]
                                    c = candle[4]
                                    v = candle[5]
                                    # Ignorar elementos adicionais se existirem
                                    
                                    self.data.append({
                                        'timestamp': int(ts),
                                        'open': float(o),
                                        'high': float(h),
                                        'low': float(l),
                                        'close': float(c),
                                        'volume': float(v),
                                        'symbol': symbol,
                                        'interval': interval
                                    })
                                
                                print(f"OK ({len(candles)} candles)")
                                
                                # Atualizar tempo para próxima requisição
                                if candles:
                                    current_time = int(candles[0][0]) + 1
                                else:
                                    break
                            else:
                                print(f"ERRO: {data.get('retMsg')}")
                                break
                        else:
                            print(f"HTTP {resp.status}")
                            break
                    
                    # Rate limit - Bybit permite ~10 requests/segundo
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    print(f"ERRO: {e}")
                    break
            
            print(f"\n[OK] Baixados {len(self.data)} candles em {request_count} requisições")
    
    def save_to_csv(self, filename: str = "bitcoin_historical_data.csv"):
        """Salva dados em CSV"""
        if not self.data:
            print("[ERRO] Nenhum dado para salvar")
            return
        
        Path("data").mkdir(exist_ok=True)
        filepath = f"data/{filename}"
        
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol', 'interval'
                ])
                writer.writeheader()
                writer.writerows(self.data)
            
            print(f"[OK] Dados salvos em {filepath}")
            print(f"[INFO] {len(self.data)} candles em {filepath}")
            
            # Mostrar amostra
            if self.data:
                first = self.data[0]
                last = self.data[-1]
                print(f"\nAmostra:")
                print(f"  Primeiro: {datetime.fromtimestamp(first['timestamp']/1000)} - Close: ${first['close']:.2f}")
                print(f"  Último:   {datetime.fromtimestamp(last['timestamp']/1000)} - Close: ${last['close']:.2f}")
        
        except Exception as e:
            print(f"[ERRO] Falha ao salvar: {e}")
    
    def save_to_json(self, filename: str = "bitcoin_historical_data.json"):
        """Salva dados em JSON"""
        if not self.data:
            print("[ERRO] Nenhum dado para salvar")
            return
        
        Path("data").mkdir(exist_ok=True)
        filepath = f"data/{filename}"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.data, f, indent=2)
            
            print(f"[OK] Dados salvos em {filepath}")
        
        except Exception as e:
            print(f"[ERRO] Falha ao salvar: {e}")

async def main():
    """Função principal"""
    downloader = BybitHistoricalDownloader()
    
    # Configurações
    symbol = "BTCUSDT"
    interval = "5"  # 5 minutos
    days = 90  # Últimos 3 meses
    
    print("="*80)
    print("DOWNLOAD DE DADOS HISTÓRICOS - BITCOIN")
    print("="*80)
    print(f"Símbolo: {symbol}")
    print(f"Intervalo: {interval} minutos")
    print(f"Período: últimos {days} dias")
    print("="*80)
    
    # Baixar dados
    await downloader.download_klines(symbol, interval, days)
    
    # Salvar
    downloader.save_to_csv(f"btc_5min_{days}d.csv")
    downloader.save_to_json(f"btc_5min_{days}d.json")
    
    print("\n" + "="*80)
    print("Download concluído com sucesso!")
    print("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[CANCELADO] Download interrompido pelo usuário")
    except Exception as e:
        print(f"\n[ERRO] Falha fatal: {e}")
        import traceback
        traceback.print_exc()
