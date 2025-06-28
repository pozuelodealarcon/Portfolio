import yfinance as yf
import pandas as pd
import ta

def check_momentum_conditions(ticker: str) -> dict:
    result = {
        'ma_crossover': False,
        'return_20d': False,
        'rsi_rebound': False,
        'macd_golden_cross': False
    }

    try:
        # 데이터 다운로드 (auto_adjust=True 유지)
        df_momentum = yf.download(ticker, period='3mo', interval='1d', progress=False, auto_adjust=True)

        # 멀티인덱스 컬럼일 경우 첫 번째 레벨로 컬럼명 변경
        if isinstance(df_momentum.columns, pd.MultiIndex):
            df_momentum.columns = df_momentum.columns.get_level_values(0)

        if df_momentum.empty:
            print(f"[Error] Empty DataFrame for ticker {ticker}")
            return result

        if 'Close' not in df_momentum.columns:
            print(f"[Error] 'Close' column missing for {ticker}. Columns: {df_momentum.columns.tolist()}")
            return result

        # 결측치 처리 (전일 종가로 보간)
        df_momentum['Close'] = df_momentum['Close'].ffill()

        if df_momentum['Close'].isna().all():
            print(f"[Error] All 'Close' values are NaN for {ticker}")
            return result

        if len(df_momentum) < 22:
            print(f"[Warning] Not enough data rows for 20-day return calculation for {ticker} (rows={len(df_momentum)})")
            return result

        # 이동평균선 계산
        df_momentum['MA5'] = df_momentum['Close'].rolling(window=5).mean()
        df_momentum['MA20'] = df_momentum['Close'].rolling(window=20).mean()

        if pd.notna(df_momentum['MA5'].iloc[-1]) and pd.notna(df_momentum['MA20'].iloc[-1]):
            if df_momentum['MA5'].iloc[-1] > df_momentum['MA20'].iloc[-1]:
                result['ma_crossover'] = True

        # 20일 수익률 계산
        try:
            return_20d = (df_momentum['Close'].iloc[-1] / df_momentum['Close'].iloc[-21] - 1) * 100
            if return_20d >= 10:
                result['return_20d'] = True
        except IndexError:
            print(f"[Warning] Not enough data for 20-day return calculation for {ticker}")

        try:
            rsi = ta.momentum.RSIIndicator(df_momentum['Close'], window=14).rsi()
            # print("RSI tail:\n", rsi.tail(5))  # 값 확인용 출력

            if len(rsi) >= 2 and pd.notna(rsi.iloc[-2]) and pd.notna(rsi.iloc[-1]):
                if (rsi.iloc[-2] < 35 and rsi.iloc[-1] > rsi.iloc[-2]) or (30 <= rsi.iloc[-1] <= 50 and rsi.iloc[-1] > rsi.iloc[-2]):
                    result['rsi_rebound'] = True

        except Exception as e:
            print(f"[RSI Error] {ticker}: {e}")


        # MACD 골든크로스 체크
        try:
            macd_obj = ta.trend.MACD(df_momentum['Close'])
            macd_line = macd_obj.macd()
            signal_line = macd_obj.macd_signal()

            if len(macd_line) >= 2 and pd.notna(macd_line.iloc[-1]) and pd.notna(signal_line.iloc[-1]):
                cross = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
                if cross.iloc[-5:].any():  # 최근 5일 내 골든크로스 발생 여부 확인
                    result['macd_golden_cross'] = True
        except Exception as e:
            print(f"[MACD Error] {ticker}: {e}")


    except Exception as e:
        print(f"[Download Error] Ticker {ticker}: {e}")

    return result

def check_momentum_conditions_batch(tickers: list) -> pd.DataFrame:
    results = []
    for ticker in tickers:
        print(f"Processing {ticker} ...")
        res = check_momentum_conditions(ticker)
        res['Ticker'] = ticker
        results.append(res)
    # 결과 리스트를 DataFrame으로 변환 (Ticker 컬럼 첫 칼럼으로 이동)
    df_results = pd.DataFrame(results)
    cols = ['Ticker'] + [c for c in df_results.columns if c != 'Ticker']
    df_results = df_results[cols]
    return df_results

df_batch_result = check_momentum_conditions_batch(['005930.KS'])
print(type(df_batch_result.loc[df_batch_result['Ticker'] == '005930.KS', 'ma_crossover'].values[0]))
print(df_batch_result.loc[df_batch_result['Ticker'] == '005930.KS', 'return_20d'].values[0])
print(df_batch_result.loc[df_batch_result['Ticker'] == '005930.KS', 'rsi_rebound'].values[0])
print(df_batch_result.loc[df_batch_result['Ticker'] == '005930.KS', 'macd_golden_cross'].values[0])
    # 엑셀 저장 예시
    # df_batch_result.to_excel('momentum_results.xlsx', index=False)
