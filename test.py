import pandas as pd
import os

def check_cache_file(cache_file="yf_cache_multi.csv"):
    if not os.path.exists(cache_file):
        print(f"❌ 파일이 존재하지 않습니다: {cache_file}")
        return

    try:
        cache = pd.read_csv(cache_file, header=[0,1], index_col=0, parse_dates=True)
    except Exception as e:
        print(f"❌ 파일 로드 중 에러 발생: {e}")
        return

    if not isinstance(cache.columns, pd.MultiIndex):
        print("❌ 컬럼이 MultiIndex가 아닙니다.")
        print(f"컬럼들: {cache.columns}")
        return
    else:
        print("✅ 컬럼이 MultiIndex입니다.")

    print(f"컬럼 레벨 0: {cache.columns.levels[0].tolist()}")
    print(f"컬럼 레벨 1: {cache.columns.levels[1].tolist()}")

    if not pd.api.types.is_datetime64_any_dtype(cache.index):
        print("❌ 인덱스가 datetime 타입이 아닙니다.")
    else:
        print("✅ 인덱스가 datetime 타입입니다.")

    print(f"인덱스 시작일: {cache.index.min()}")
    print(f"인덱스 종료일: {cache.index.max()}")

    print("\n캐시 데이터 샘플 (앞 5줄):")
    print(cache.head())
    print("\n캐시 데이터 샘플 (뒤 5줄):")
    print(cache.tail())

    # 여기 수정된 부분! 컬럼 레벨 1이 'Close'인 컬럼들 선택
    close_cols = [col for col in cache.columns if col[1] == 'Close']
    if not close_cols:
        print("❌ 'Close' 컬럼이 존재하지 않습니다.")
    else:
        print(f"✅ 'Close' 컬럼 개수: {len(close_cols)}")
        for col in close_cols[:3]:
            series = cache[col]
            na_count = series.isna().sum()
            print(f"  - {col}: NaN 개수 = {na_count} / 전체 행 = {len(series)}")

check_cache_file("yf_cache_multi.csv")
