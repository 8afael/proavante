import yfinance as yf
import pytz
from datetime import datetime
import pandas as pd
from pprintpp import pprint
from yahoofinance import IncomeStatementQuarterly

class getInfo:

    def fetch_stock_data(self, ticker, parameter):
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            info = stock.info
            
            if hist.empty:
                raise ValueError(f"No data found for ticker: {ticker}")

            if parameter in info:
                return info[parameter]
            else:
                return f"Parameter '{parameter}' not found in stock info."

        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")


    def getCurrentPrice(self, ticker):
        stock = yf.Ticker(ticker)
        currentPrice = stock.info['currentPrice']
        pprint(f"Current Price: {ticker} Value: {currentPrice}")
        return currentPrice
    
    def getBookValue(self, ticker, parameter):
        bookValue = self.fetch_stock_data(ticker, parameter)
        pprint(f"Book Value {ticker} Value: {bookValue}")
        return bookValue
    
    def dividendYield(self, ticker):
        stock = yf.Ticker(ticker)
        dividendYear = stock.info['dividendYield']
        pprint(f"Dividend Yield: {ticker} Value: {dividendYear}")
        return dividendYear
    
    def getDividendFiveYears(self, ticker):
        stock = yf.Ticker(ticker)
        dividend5Year = stock.info['fiveYearAvgDividendYield']
        pprint(f"Average dividends last 5 Years: {ticker} Value: {dividend5Year}")
        return dividend5Year

    def getAllInfo(self, ticker):
        stock = yf.Ticker(ticker)
        info = stock.info
        pprint(f"Ticker: {ticker} Info: {info}")
        return info



