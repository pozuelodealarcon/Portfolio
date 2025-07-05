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
import yfinance as yf

import yfinance as yf

import yfinance as yf

import yfinance as yf

def get_percentage_change_1mo(ticker):
    ticker_obj = yf.Ticker(ticker)

    # Get last 1 month of price data
    data = ticker_obj.history(period="1mo")

    if len(data) >= 2:
        start_close = data['Close'].iloc[0]
        end_close = data['Close'].iloc[-1]

        if start_close != 0:
            percent_change = ((end_close - start_close) / start_close) * 100
            sign = "+" if percent_change >= 0 else ""
            return f" ({sign}{percent_change:.2f}%)"
        else:
            return " ()"
    else:
        return " ()"

print(get_percentage_change_1mo("nvda"))  # Example usage