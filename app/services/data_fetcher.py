# Exemplo de serviço (app/services/data_fetcher.py)
import yfinance as yf
from typing import Dict
import pandas as pd

class MarketDataService:
    @staticmethod
    def get_real_time_quote(symbol: str) -> Dict:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d")
        if data.empty:
            return {"error": "Símbolo não encontrado"}
        latest = data.iloc[-1]
        return {
            "symbol": symbol,
            "price": latest['Close'],
            "open": latest['Open'],
            "high": latest['High'],
            "low": latest['Low'],
            "volume": latest['Volume']
        }

    @staticmethod
    def get_historical_data(symbol: str, period: str = "6mo") -> pd.DataFrame:
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period)