import yfinance as yf
from datetime import datetime, timedelta

ticker = "NSC"
end_date = datetime.today()
start_date = end_date - timedelta(days=365)

print(f"Downloading {ticker} from {start_date.date()} to {end_date.date()}...")
df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

print("\n=== Data Head ===")
print(df.head())

print("\n=== Data Columns ===")
print(df.columns)

# Handle MultiIndex safely
try:
    close_data = df.xs("Close", level=0, axis=1)
    if close_data.isna().all().all():
        print(f"\n❌ '{ticker}' has only NaNs in Close prices.")
    else:
        print(f"\n✅ '{ticker}' has valid Close price data.")
except KeyError:
    print(f"\n❌ 'Close' level not found in columns — maybe data is missing or malformed.")
