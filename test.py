import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 🔹 종목 불러오기 (삼성전자 예시)
ticker = '005930.KS' # 삼성전자 한국 종목
df = yf.download(ticker, period='6mo', interval='1d')

# 🔹 최근 N일 중 가장 자주 출현한 저가 범위 찾기 (예: 지지선 후보)
N = 60
recent_lows = df['Low'].tail(N)
rounded_lows = recent_lows.round(-2) # 소수점 제거하고 100단위로 반올림

support_level = rounded_lows.value_counts().idxmax()
print(f"예상 지지선: {support_level}원")

# 🔹 차트 시각화
plt.figure(figsize=(12,6))
plt.plot(df['Close'], label='종가')
plt.axhline(y=support_level, color='green', linestyle='--', label=f'지지선 약 {support_level}원')
plt.title(f'{ticker} 지지선 예측')
plt.legend()
plt.grid()
plt.show()

