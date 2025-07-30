import yfinance as yf
from datetime import datetime, date


def get_percentage_change_ttm(ticker):
    ticker_obj = yf.Ticker(ticker)

    # Get start of the current month
    today = date.today()
    start_of_month = today.replace(day=1)

    # Fetch price data from start of month to today
    data = ticker_obj.history(start=start_of_month, end=today)

    if len(data) >= 2:
        start_close = data["Close"].iloc[0]
        end_close = data["Close"].iloc[-1]

        if start_close != 0:
            percent_change = ((end_close - start_close) / start_close) * 100
            sign = "+" if percent_change >= 0 else ""
            return f" ({sign}{percent_change:.2f}%)"
        else:
            return " ()"
    else:
        return " ()"


print(get_percentage_change_ttm("crcl"))  # Example usage
