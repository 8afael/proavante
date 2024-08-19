import asyncio
from dashboard.yahoo import getInfo
from dashboard.finhub import hub

class Main:

    async def main():
        ticker = "PETR3.SA"
        #dividend = "dividendYield"
        #bookValue = "bookValue"
        getInfoTicker = getInfo()
        getInfoTicker.getCurrentPrice(ticker)      
        #getInfoTicker.getBookValue(ticker, bookValue)
        #getInfoTicker.getAllInfo(ticker)
        getInfoTicker.dividendYield(ticker)
        getInfoTicker.getDividendFiveYears(ticker)

        #hub.start() # FinnHub

    asyncio.run(main())