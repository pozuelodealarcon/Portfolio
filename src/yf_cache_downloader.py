import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

CACHE_FILE = "yf_cache_multi.csv"
limit = 200
api_key = os.environ['FMP_API_KEY']

#hi
def get_tickers_by_country(country:str, limit: int, apikey: str):
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

def get_business_days(start_date, end_date):
    return pd.bdate_range(start=start_date, end=end_date)

def download_yf_data(tickers, start_date, end_date, interval="1d"):
    df = yf.download(tickers, start=start_date, end=end_date, interval=interval, auto_adjust=True, progress=False, group_by='ticker')
    # If only one ticker, add a top-level column for consistency
    if isinstance(tickers, str) or len(tickers) == 1:
        df = pd.concat({tickers[0] if isinstance(tickers, list) else tickers: df}, axis=1)
    df.index = pd.to_datetime(df.index)
    return df

def update_cache(tickers, cache_file=CACHE_FILE):
    today = datetime.today().date()
    one_year_ago = today - timedelta(days=365)
    business_days = get_business_days(one_year_ago, today)

    if os.path.exists(cache_file):
        cache = pd.read_csv(cache_file, header=[0,1], index_col=0, parse_dates=True)
    else:
        cache = pd.DataFrame()

    # Use the first available business day as the start date
    if len(business_days) > 0:
        start_date = business_days[0]
    else:
        start_date = today  # fallback, should not happen

    # Find missing days for each ticker
    missing_days = []
    for ticker in tickers:
        if (ticker, 'Close') not in cache.columns:
            missing_days = business_days
            break
        missing = [d for d in business_days if d not in cache.index or pd.isna(cache.loc[d, (ticker, 'Close')])]
        missing_days.extend(missing)
    missing_days = sorted(set(missing_days))

    if missing_days:
        start = min(missing_days).strftime("%Y-%m-%d")
        end = (max(missing_days) + timedelta(days=1)).strftime("%Y-%m-%d")
        new_data = download_yf_data(tickers, start, end)
        if cache.empty:
            cache = new_data
        else:
            cache = pd.concat([cache, new_data[~new_data.index.isin(cache.index)]])
            cache = cache.sort_index()
            cache = cache.loc[~cache.index.duplicated(keep='last')]
        cache.to_csv(cache_file)

    # Ensure all business days are present (fill missing with NaN)
    cache = cache.reindex(business_days)
    return cache

if __name__ == "__main__":
    tickers = get_tickers_by_country('US', limit, api_key)  # Example tickers
    tickers_to_remove = ['ANTM', 'ACH', 'RY-PT', 'VZA','AED', 'AEH', 'BDXA', 'AMOV', 'PXD', 'ATVI', 'SQ', 'CEO']
    tickers = [t for t in tickers if t not in tickers_to_remove]
    print(len(tickers))
    update_cache(tickers)