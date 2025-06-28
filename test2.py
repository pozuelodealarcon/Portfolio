import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def get_support_price(ticker: str, period: str = '1y', tolerance: float = 0.01, bins: int = 30, plot=False):
    # 데이터 불러오기
    df = yf.download(ticker, period=period)
    if df.empty or len(df) < 60:
        print("데이터 부족")
        return None

    # 컬럼 체크
    if 'Close' not in df.columns:
        raise ValueError("다운로드한 데이터에 'Close' 컬럼이 없습니다.")
    
    # MA60 계산
    df['MA60'] = df['Close'].rolling(window=60).mean()

    # MA60 유효한 기간만 필터링
    if 'MA60' not in df.columns:
        raise ValueError("'MA60' 컬럼 생성 실패")
    df = df.dropna(subset=['MA60'])

    # MA60 근처에서 반등한 Low 추출
    cond = (df['Low'] >= df['MA60'] * (1 - tolerance)) & (df['Low'] <= df['MA60'] * (1 + tolerance))
    df_near_ma = df[cond]

    if df_near_ma.empty:
        print("MA60 근처 반등 데이터 없음")
        return None

    # 히스토그램 분석으로 지지선 후보 추출
    counts, edges = np.histogram(df_near_ma['Low'], bins=bins)
    max_bin_index = np.argmax(counts)
    support_zone = (edges[max_bin_index], edges[max_bin_index + 1])
    support_price = round((support_zone[0] + support_zone[1]) / 2, 2)

    if plot:
        plt.figure(figsize=(10, 5))
        plt.hist(df_near_ma['Low'], bins=bins, color='skyblue', edgecolor='black')
        plt.axvline(support_price, color='red', linestyle='--', label=f'추정 지지선: {support_price}')
        plt.title(f"{ticker} - MA60 근처 반등 가격 분포")
        plt.xlabel("가격대")
        plt.ylabel("빈도")
        plt.legend()
        plt.grid(True)
        plt.show()

    return support_price
support = get_support_price("005930.KS", plot=True)
print("추정 지지선:", support)
