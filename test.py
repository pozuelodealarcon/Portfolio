import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import ta
import yfinance as yf
import pandas as pd

def get_trading_volume_vs_avg20(ticker_symbol: str) -> float:
    try:
        # Fetch 21 days of data
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="21d")

        if len(hist) < 21:
            return None  # Not enough data

        today_volume = hist["Volume"].iloc[-1]
        avg_volume_20 = hist["Volume"].iloc[:-1].mean()

        if avg_volume_20 == 0 or pd.isna(today_volume) or pd.isna(avg_volume_20):
            return None  # Invalid data

        # Return ratio (e.g., 1.5 means 150% of avg volume)
        return round(today_volume / avg_volume_20, 1)

    except Exception as e:
        print(f"[Error] {ticker_symbol}: {e}")
        return None


ratio = get_trading_volume_vs_avg20("ORCL")
print(ratio)  # → e.g., 1.52
