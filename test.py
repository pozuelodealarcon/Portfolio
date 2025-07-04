import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ta
import yfinance as yf
import pandas as pd

import yfinance as yf
import datetime as dt
import requests

import requests

def get_us_tickers_by_market_cap(limit: int, apikey: str):
    url = 'https://financialmodelingprep.com/api/v3/stock-screener'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    exchanges = ['nyse', 'nasdaq', 'amex']
    all_stocks = []

    try:
        for exchange in exchanges:
            params = {
                'exchange': exchange,
                'limit': 500,  # 넉넉히 가져오기
                'type': 'stock',
                'isEtf': False,
                'isFund': False,
                'apikey': apikey,
            }
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            all_stocks.extend(data)

        # 시가총액 기준 정렬
        sorted_stocks = sorted(
            all_stocks,
            key=lambda x: x.get('marketCap', 0),
            reverse=True
        )

        # 중복 제거 및 상위 limit만 추출
        seen = set()
        unique_sorted = []
        for stock in sorted_stocks:
            symbol = stock.get("symbol")
            if symbol and symbol not in seen:
                seen.add(symbol)
                unique_sorted.append(symbol)
            if len(unique_sorted) >= limit:
                break

        return unique_sorted

    except Exception as e:
        print(f"Error: {e}")
        return []



print(get_us_tickers_by_market_cap(300, ''))