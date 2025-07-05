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

def get_fcf_yield_and_cagr(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)

        # 1. Market cap
        market_cap = ticker_obj.info.get('marketCap')
        if market_cap is None or market_cap == 0:
            return (None, None, "Market cap unavailable")

        # 2. Cash flow DataFrame
        cashflow_df = ticker_obj.cashflow
        if cashflow_df.empty or 'Free Cash Flow' not in cashflow_df.index:
            return (None, None, "Free Cash Flow data unavailable")

        # 3. Get FCF series (drop NaNs and reverse to oldest -> newest)
        fcf_series = cashflow_df.loc['Free Cash Flow'].dropna()
        fcf_series = fcf_series[::-1]  # chronological order

        if len(fcf_series) < 2:
            return (None, None, "Insufficient FCF history for CAGR")

        fcf_data = fcf_series.tolist()

        # 4. FCF Yield = latest FCF / market cap
        latest_fcf = fcf_series.iloc[-1]
        if latest_fcf == 0:
            fcf_yield = 0.0
        else:
            fcf_yield = round((latest_fcf / market_cap) * 100, 2)

        # 5. FCF CAGR calculation
        initial_fcf = fcf_series.iloc[0]
        final_fcf = fcf_series.iloc[-1]
        n_years = len(fcf_series) - 1

        if initial_fcf <= 0 or final_fcf <= 0:
            fcf_cagr = None  # Cannot compute CAGR with non-positive values
        else:
            fcf_cagr = round(((final_fcf / initial_fcf) ** (1 / n_years) - 1) * 100, 2)

        return (fcf_yield, fcf_cagr, fcf_data)

    except Exception as e:
        return (None, None, f"Error: {str(e)}")



def get_10yr_treasury_yield():
    try:
        tnx = yf.Ticker("^TNX")
        tnx_data = tnx.history(period="1d")
        latest_yield = tnx_data['Close'].iloc[-1]
        return round(latest_yield, 2)  # Already in percent
    except Exception as e:
        return f"Error fetching yield: {e}"


def dcf_valuation(fcf_history, discount_rate, long_term_growth, years=10, shares_outstanding=None):
    if not fcf_history or len(fcf_history) < 2:
        return (None, None)

    start_fcf = fcf_history[0]  # oldest
    end_fcf = fcf_history[-1]   # most recent

    if start_fcf <= 0 or end_fcf <= 0:
        return (None, None)

    if discount_rate <= long_term_growth:
        return (None, None)  # Invalid terminal growth assumption

    # CAGR and growth rate
    cagr = (end_fcf / start_fcf) ** (1 / (len(fcf_history) - 1)) - 1
    growth_rate = min(cagr, discount_rate)

    # Project FCFs
    projected_fcfs = [end_fcf * (1 + growth_rate) ** i for i in range(1, years + 1)]

    # Terminal Value
    terminal_value = projected_fcfs[-1] * (1 + long_term_growth) / (discount_rate - long_term_growth)

    # Discounting
    discounted_fcfs = [fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(projected_fcfs, 1)]
    discounted_terminal_value = terminal_value / ((1 + discount_rate) ** years)

    enterprise_value = sum(discounted_fcfs) + discounted_terminal_value

    if shares_outstanding is None or shares_outstanding <= 0:
        return (None, None)

    intrinsic_value = enterprise_value / shares_outstanding

    return float(intrinsic_value), round(growth_rate * 100, 2)


# Example usage:
ticker = "AAPL"  # Example ticker
info = yf.Ticker(ticker).info
shares_outstanding = info.get('sharesOutstanding')
fcf_yield, fcf_cagr, fcf_list = get_fcf_yield_and_cagr(ticker)
print(fcf_list)
tenyr_treasury_yield = get_10yr_treasury_yield()
print(tenyr_treasury_yield)
discount_rate = (tenyr_treasury_yield+5.0)/100.0
print(dcf_valuation(fcf_list, discount_rate=discount_rate, long_term_growth=0.02, years=10, shares_outstanding=shares_outstanding))