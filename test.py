import yfinance as yf
ticker = yf.Ticker("NVDA")
hist = ticker.history(period="3d").tail(3)
print(hist)
if len(hist) < 2:
    print('a')

price_today = hist['Close'].iloc[1]
price_yesterday = hist['Close'].iloc[0]

change = price_today - price_yesterday
percent_change = (change / price_yesterday) * 100

sign = "▲" if change > 0 else "▼" if change < 0 else "-"
print({
    "price": round(price_today, 2),
    "change": f"{sign} {abs(percent_change):.2f}%"
})