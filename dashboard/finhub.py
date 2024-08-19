import finnhub
import os


class hub:

    def start():
        key = "cqvdojhr01qkoahfsfe0cqvdojhr01qkoahfsfeg"  # cqvdojhr01qkoahfsfe0cqvdojhr01qkoahfsfeg
        #finnhub_client = finnhub.Client(api_key=key)
        finnhub_client = finnhub.Client(api_key=[key])

        # Stock candles
        res = finnhub_client.company_historical_esg_score('AAPL')
        print(res)