import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# --- CONFIGURATION ---
CACHE_FILE = "yf_cache_multi.csv"  # Path to your cached price data
BENCHMARK = "^GSPC"                # S&P 500
REBALANCE_FREQ = "M"               # Monthly rebalancing
TOP_N = 5           # Number of top stocks to hold
START_DATE = "2025-01-01"          # Backtest start
END_DATE = datetime.today().strftime("%Y-%m-%d")  # Backtest end

# --- LOAD PRICE DATA ---
cache = pd.read_csv(CACHE_FILE, header=[0,1], index_col=0, parse_dates=True)
# Only keep 'Close' prices
if isinstance(cache.columns, pd.MultiIndex):
    close_columns = [col for col in cache.columns if col[1] == 'Close']
    price_df = cache[close_columns]
    price_df.columns = [col[0] for col in price_df.columns]
else:
    price_df = cache[['Close']]
    price_df.columns = ['Close']

# Filter by date
price_df = price_df[(price_df.index >= START_DATE) & (price_df.index <= END_DATE)]

# Drop columns with too many missing values
price_df = price_df.dropna(axis=1, thresh=int(0.8 * len(price_df)))

# --- LOAD YOUR LATEST SCORING (from Excel) ---
score_df = pd.read_excel("deep_fund.xlsx", sheet_name="종목분석")
score_df = score_df.rename(columns={"티커": "Ticker"})

# --- BENCHMARK DATA ---
benchmark = yf.download(BENCHMARK, start=START_DATE, end=END_DATE, progress=False, auto_adjust=True)["Close"]

# --- LOAD WEIGHTS FROM '포트비중_Sortino' SHEET ---
sortino_df = pd.read_excel("deep_fund.xlsx", sheet_name="포트비중_Sortino")
# 예시: 'Ticker', 'Weight' 컬럼이 있다고 가정
sortino_weights = dict(zip(sortino_df['티커'], sortino_df['비중(%)']))

# --- BACKTEST FUNCTION ---
def backtest(price_df, score_df, benchmark, top_n=TOP_N, rebalance_freq=REBALANCE_FREQ):
    price_df = price_df.ffill().dropna()
    rebal_dates = price_df.resample('ME').last().index

    portfolio_value = [1.0]
    dates = [price_df.index[0]]
    weights_history = []
    tickers_history = []

    for i in range(1, len(rebal_dates)):
        date = rebal_dates[i]
        prev_date = rebal_dates[i-1]
        if date not in price_df.index:
            date_idx = price_df.index.searchsorted(date, side='right') - 1
            if date_idx < 0:
                continue
            date = price_df.index[date_idx]
        if prev_date not in price_df.index:
            prev_idx = price_df.index.searchsorted(prev_date, side='right') - 1
            if prev_idx < 0:
                continue
            prev_date = price_df.index[prev_idx]

        # 포트비중_Sortino 시트의 티커와 비중 사용
        available = [t for t in sortino_weights if t in price_df.columns]
        if len(available) == 0:
            continue
        weights = np.array([sortino_weights[t] for t in available])
        weights = weights / weights.sum()  # 혹시 합이 1이 아닐 경우 정규화

        start_prices = price_df.loc[prev_date, available]
        end_prices = price_df.loc[date, available]
        period_return = np.dot((end_prices.values / start_prices.values) - 1, weights)
        portfolio_value.append(portfolio_value[-1] * (1 + period_return))
        dates.append(date)
        weights_history.append(dict(zip(available, weights)))
        tickers_history.append(available)

    # Benchmark
    bench = benchmark.reindex(dates).ffill()
    bench_returns = bench.pct_change().fillna(0)
    bench_value = (1 + bench_returns).cumprod().values

    min_len = min(len(dates), len(portfolio_value), len(bench_value))
    results = pd.DataFrame({
        "Date": np.array(dates[:min_len]).ravel(),
        "Portfolio": np.array(portfolio_value[:min_len]).ravel(),
        "Benchmark": np.array(bench_value[:min_len]).ravel()
    }).set_index("Date")

    return results, weights_history, tickers_history

# --- RUN BACKTEST ---
results, weights_history, tickers_history = backtest(price_df, score_df, benchmark, top_n=TOP_N)

# --- PERFORMANCE METRICS ---
def max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

def annualized_return(series):
    total_return = series.iloc[-1] / series.iloc[0] - 1
    years = (series.index[-1] - series.index[0]).days / 365.25
    return (1 + total_return) ** (1 / years) - 1

def annualized_volatility(series):
    returns = series.pct_change().dropna()
    return returns.std() * np.sqrt(12)

def sharpe_ratio(series, risk_free=0.02):
    ann_ret = annualized_return(series)
    ann_vol = annualized_volatility(series)
    return (ann_ret - risk_free) / ann_vol if ann_vol > 0 else np.nan

print("=== Backtest Results ===")
print(f"Portfolio Annualized Return: {annualized_return(results['Portfolio']):.2%}")
print(f"Portfolio Annualized Volatility: {annualized_volatility(results['Portfolio']):.2%}")
print(f"Portfolio Max Drawdown: {max_drawdown(results['Portfolio']):.2%}")
print(f"Portfolio Sharpe Ratio: {sharpe_ratio(results['Portfolio']):.2f}")
print(f"Benchmark Annualized Return: {annualized_return(results['Benchmark']):.2%}")
print(f"Benchmark Max Drawdown: {max_drawdown(results['Benchmark']):.2%}")

# --- PLOT ---
import matplotlib.pyplot as plt
plt.figure(figsize=(12,6))
plt.plot(results.index, results["Portfolio"], label="Buffett US Portfolio")
plt.plot(results.index, results["Benchmark"], label="S&P 500")
plt.title("Portfolio vs Benchmark")
plt.ylabel("Cumulative Return (Growth of $1)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()