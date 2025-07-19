import yfinance as yf
import os

tnx = yf.Ticker("^TNX")
tnx_data = tnx.history(period="1d")
latest_yield = tnx_data['Close'].iloc[-1]
risk_free_rate = round(latest_yield / 100.0, 2)
print(f"Risk-free rate (10-year Treasury yield): {risk_free_rate}")