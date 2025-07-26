import pandas as pd

# 1. 캐시 불러오기 (파일 경로 맞춰 주세요)
cache = pd.read_csv('yf_cache_multi.csv', header=[0, 1], index_col=0, parse_dates=True)

# 2. 예시 ticker 리스트
tickers = ['GOOG', 'GOOGL', 'AAPL', 'MSFT', 'FAKE1', 'FAKE2']  # FAKE1, FAKE2는 실패한 티커라고 가정

# 3. 성공적으로 다운로드된 티커만 추출
if isinstance(cache.columns, pd.MultiIndex):
    successful_tickers = set([col[0] for col in cache.columns if col[1] == 'Close'])
else:
    successful_tickers = set(cache.columns)

# 4. 필터링된 티커 리스트
filtered_tickers = [t for t in tickers if t in successful_tickers]

# 5. 결과 출력
print("✅ Cache에 존재하는 Close 데이터 있는 티커들:", successful_tickers)
print("🎯 원래 티커 리스트:", tickers)
print("🎯 필터링된 최종 티커 리스트:", filtered_tickers)
