# Ubicación: trading-system/data/data_fetcher.py

import ccxt
import pandas as pd

class DataFetcher:
    def __init__(self):
        # Usamos Binance como fuente principal (público, no requiere API Key para ver precios)
        self.exchange = ccxt.binance()

    def get_latest_price(self, symbol="BTC/USDT"):
        """Trae el precio actual (Ticker)"""
        ticker = self.exchange.fetch_ticker(symbol)
        return ticker['last']

    def get_historical_data(self, symbol="BTC/USDT", timeframe='1h', limit=100):
        """Trae velas japonesas (OHLCV) para análisis técnico"""
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    def get_rsi(self, symbol="BTC/USDT", period=14):
        """Calcula el RSI para saber si el mercado está caro o barato"""
        # 1. Traemos las últimas 100 velas de 1 hora
        df = self.get_historical_data(symbol, timeframe='1h', limit=100)
        
        # 2. Calculamos la diferencia de precios
        delta = df['close'].diff()
        
        # 3. Lógica matemática del RSI
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Retornamos el último valor del RSI
        return df['rsi'].iloc[-1]
    def get_all_usdt_symbols(self):
        """Busca todos los pares que cotizan contra USDT con volumen real"""
        markets = self.exchange.load_markets()
        # Filtramos: que sea contra USDT y que esté activo
        symbols = [s for s, m in markets.items() if '/USDT' in s and m['active']]
        return symbols
    def get_sma(self, symbol="BTC/USDT", period=20):
        """Calcula la Media Móvil Simple para identificar la tendencia"""
        df = self.get_historical_data(symbol, timeframe='1h', limit=period + 1)
        sma = df['close'].rolling(window=period).mean()
        return sma.iloc[-1]
    def get_volatility(self, symbol="BTC/USDT", period=14):
        """Calcula el ATR (Average True Range) para medir la volatilidad"""
        try:
            # Traemos 1H de data histórica (limit=period+5 para el margen)
            df = self.get_historical_data(symbol, timeframe='1h', limit=period + 5)
            
            # Cálculo de True Range (TR)
            df['tr1'] = abs(df['high'] - df['low'])
            df['tr2'] = abs(df['high'] - df['close'].shift())
            df['tr3'] = abs(df['low'] - df['close'].shift())
            
            df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # ATR es la SMA del True Range
            atr = df['true_range'].rolling(window=period).mean().iloc[-1]
            return atr
        except:
            return 0.0