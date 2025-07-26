import pandas as pd

def test_close_price_extraction(cache_file="yf_cache_multi.csv", days=365):
    print(f"Loading cache file: {cache_file}")
    try:
        cache = pd.read_csv(cache_file, header=[0,1], index_col=0, parse_dates=True)
    except Exception as e:
        print(f"❌ Failed to load cache file: {e}")
        return

    print("Cache loaded. Columns:", cache.columns)
    print("Cache index range:", cache.index.min(), "to", cache.index.max())

    end_date = pd.Timestamp.today().normalize()
    start_date = end_date - pd.Timedelta(days=days)

    # 날짜 범위를 cache index 범위 내로 맞춤
    start_date = max(start_date, cache.index.min())
    end_date = min(end_date, cache.index.max())

    print(f"Slicing cache from {start_date.date()} to {end_date.date()}")
    cache_slice = cache.loc[start_date:end_date]

    if isinstance(cache_slice.columns, pd.MultiIndex):
        close_cols = [col for col in cache_slice.columns if col[1] == 'Close']
        df_close = cache_slice[close_cols].copy()
        df_close.columns = [col[0] for col in df_close.columns]
    else:
        if 'Close' in cache_slice.columns:
            df_close = cache_slice[['Close']].copy()
            df_close.columns = ['Close']
        else:
            print("❌ 'Close' column not found in cache.")
            return

    # NaN 컬럼 제거
    df_close.dropna(axis=1, how='all', inplace=True)

    print(f"Close prices DataFrame shape: {df_close.shape}")
    print("Columns (tickers):", df_close.columns.tolist())
    print("Sample data:")
    print(df_close.head())

if __name__ == "__main__":
    test_close_price_extraction()
