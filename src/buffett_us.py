# SPDX-FileCopyrightText: © 2025 Hyungsuk Choi <chs_3411@naver[dot]com>, University of Maryland 
# SPDX-License-Identifier: MIT

import yfinance as yf
import pandas as pd
import numpy as np
import requests
import string
import datetime as dt
import openpyxl
import math
from queue import Queue
import threading
import time
import polars as pl
#import shelve
from bs4 import BeautifulSoup
from urllib.request import urlopen
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
import os
import ta # 기술적 지표 계산 라이브러리
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import norm
from scipy.stats import skew, kurtosis
from scipy.stats.mstats import gmean
from datetime import datetime, timedelta
from google import genai
from google.genai import types


################ DEPENDENCIES ###########################

# pip install -r requirements.txt

#########################################################


################ PREDETERMINED FIELDS ###################

EMAIL = os.environ['EMAIL_ADDRESS']
PASSWORD = os.environ['EMAIL_PASSWORD']
# Get the API key
fmp_key = os.environ['FMP_API_KEY']
marketaux_api = os.environ['MARKETAUX_API']
recipients = ['chs_3411@naver.com', 'eljm2080@gmail.com', 'hyungsukchoi3411@gmail.com']

NUM_THREADS = 2 #multithreading 

country = 'US'
limit=100 # 250 requests/day
opt = 10 # top X tickers to optimize
sp500 = True

#########################################################

# print('May take up to few minutes...')
 
today = dt.datetime.today().weekday()
weekend = today - 4 # returns 1 for saturday, 2 for sunday
formattedDate = (dt.datetime.today() - dt.timedelta(days = weekend)).strftime("%Y%m%d") if today >= 5 else dt.datetime.today().strftime("%Y%m%d")

three_months_approx = dt.datetime.today() - dt.timedelta(days=90)
formattedDate_3m_ago =  three_months_approx.strftime("%Y%m%d")

esg_dict = {
    'LAG_PERF': '미흡',
    'AVG_PERF': '보통',
    'LEAD_PERF': '우수',
}

data = []
data_lock = threading.Lock()

def get_tickers(country: str, limit: int, sp500: bool):
    if country is not None:
        return get_tickers_by_country(country, limit, fmp_key) #US, JP, KR
    elif sp500:
        return pl.read_csv("https://datahub.io/core/s-and-p-500-companies/r/constituents.csv")["Symbol"].to_list()
    elif not sp500:
        nasdaq100_url = 'https://en.wikipedia.org/wiki/NASDAQ-100'
        nasdaq100 = pd.read_html(nasdaq100_url, header=0)[4] # Might need to adjust index (5th table on the page)
        return nasdaq100['Ticker'].tolist()
    else:
        raise Exception("No tickers list satisfies the given parameter")

def get_tickers_by_country(country:str, limit: int, apikey: str):
    url = 'https://financialmodelingprep.com/api/v3/stock-screener'
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    exchanges = ['nyse', 'nasdaq', 'amex']
    all_stocks = []

    try:
        for exchange in exchanges:
            params = {
                'exchange': exchange,
                'limit': 500,  # 넉넉히 가져오기
                'type': 'stock',
                'isEtf': False,
                'isFund': False,
                'apikey': apikey,
            }
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            all_stocks.extend(data)

        # 시가총액 기준 정렬
        sorted_stocks = sorted(
            all_stocks,
            key=lambda x: x.get('marketCap', 0),
            reverse=True
        )

        # 중복 제거 및 상위 limit만 추출
        seen = set()
        unique_sorted = []
        for stock in sorted_stocks:
            symbol = stock.get("symbol")
            if symbol and symbol not in seen:
                seen.add(symbol)
                unique_sorted.append(symbol)
            if len(unique_sorted) >= limit:
                break

        return unique_sorted

    except Exception as e:
        print(f"Error: {e}")
        return []

# buffett's philosophy & my quant ideas
def buffett_score (de, cr, pbr, per, ind_per, roe, ind_roe, roa, ind_roa, eps, div, icr, opinc_yoy, opinc_qoq):
    score = 0
    #basic buffett-style filtering
    if de is not None and de <= 0.5 and de != 0:
        score +=1
    if cr is not None and (cr >= 1.5 and cr <= 2.5):
        score +=1

    if pbr is not None and (pbr <= 2 and pbr > 0):
        score +=0.5
        if pbr <= 1.5:
            score +=1
            if pbr <= 1:
                score += 0.5
        

    # 고배당주 수혜 예상
    if div is not None and not isinstance(div, bool): #cagr = +4~6-10%
        if div >= 0.1:
            score +=1.0
        elif div >= 0.08:
            score +=0.75
        elif div >= 0.06:
            score +=0.5

    if isinstance(div, bool) and div: #3y yoy
        score +=1
    
    if isinstance(opinc_yoy, bool):
        if opinc_yoy:
            score += 1
        else: 
            score -= 1
    else:
        if opinc_yoy is not None:
            if opinc_yoy > 0:
                score += 1
            else:
                score -= 1


    if isinstance(opinc_qoq, bool):
        if opinc_qoq:
            score += 1
    else:
        if opinc_qoq is not None:
            if opinc_qoq > 0:
                score += 1


    if isinstance(eps, bool):
        if eps:
            score += 1
        else: 
            score -= 1
    else:
        if eps is not None:
            if eps >= 0.1:
                score += 1
                if div is not None:
                    if div and eps >= 0.3:
                        score +=1
        #  3. 고배당 + 고EPS 성장률 전략 (배당 성장주 전략)
        # 아이디어: 고배당이면서 실적 성장세가 뚜렷한 기업
            if eps < 0:
                score -= 1
            if eps > 0 and per is not None:
                peg = per / (eps * 100) #peg ratio, underv if less than 1
                if peg <= 1:
                    score += 1

    if icr is not None and icr >= 5: #x5
        score +=1

    if None not in {roe, ind_roe, per, ind_per}:
        if per > ind_per and roe < ind_roe:
            score -=2 # hard pass
            if roe < 0:  #EVEN WORSE
                score -=1

    if None not in {roe, ind_roe, per, ind_per, roa, ind_roa}:
        # 1. 저PER + 고ROE 전략 (가치 + 질적 우량주)
        # 아이디어: 저평가된 기업 중 자본수익률이 높은 우량주 발굴
        if roe > ind_roe and per != 0:
            if per < ind_per:
                score += 2  # strong fundamentals and value
                # if roa > ind_roa:
                #     score += 0.5
            elif per <= 1.2 * ind_per:
                score += 1  # great business, slightly overvalued (still reasonable)
                # if roa > ind_roa:
                #     score += 0.25
         
    return score

def get_fcf_yield_and_cagr(ticker, api_key="YOUR_API_KEY"):
    def try_fmp(ticker, api_key):
        try:
            # 1. Market cap
            profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={api_key}"
            profile_resp = requests.get(profile_url)
            if profile_resp.status_code != 200 or not profile_resp.json():
                return (None, None, [])

            market_cap = profile_resp.json()[0].get("mktCap")
            if market_cap is None or market_cap == 0:
                return (None, None, [])

            # 2. FCF list
            url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=10&apikey={api_key}"
            response = requests.get(url)
            if response.status_code != 200 or not response.json():
                return (None, None, [])

            data = response.json()
            fcf_list = [item['freeCashFlow'] for item in data if item.get('freeCashFlow') is not None]
            fcf_list = fcf_list[::-1]

            if len(fcf_list) < 2:
                return (None, None, fcf_list)

            # 3. FCF Yield
            latest_fcf = fcf_list[-1]
            fcf_yield = round((latest_fcf / market_cap) * 100, 2) if latest_fcf else 0.0

            # 4. FCF CAGR
            initial_fcf, final_fcf = fcf_list[0], fcf_list[-1]
            n_years = len(fcf_list) - 1
            if initial_fcf <= 0 or final_fcf <= 0:
                fcf_cagr = None
            else:
                fcf_cagr = round(((final_fcf / initial_fcf) ** (1 / n_years) - 1) * 100, 2)

            return (fcf_yield, fcf_cagr, fcf_list)

        except Exception:
            return (None, None, [])

    def try_yf(ticker):
        try:
            ticker_obj = yf.Ticker(ticker)

            market_cap = ticker_obj.info.get('marketCap')
            if market_cap is None or market_cap == 0:
                return (None, None, [])

            cashflow_df = ticker_obj.cashflow
            if cashflow_df.empty or 'Free Cash Flow' not in cashflow_df.index:
                return (None, None, [])

            fcf_series = cashflow_df.loc['Free Cash Flow'].dropna()[::-1]
            if len(fcf_series) < 2:
                return (None, None, fcf_series.tolist())

            fcf_list = fcf_series.tolist()
            latest_fcf = fcf_series.iloc[-1]
            fcf_yield = round((latest_fcf / market_cap) * 100, 2) if latest_fcf else None

            initial_fcf, final_fcf = fcf_series.iloc[0], fcf_series.iloc[-1]
            n_years = len(fcf_series) - 1
            if initial_fcf <= 0 or final_fcf <= 0:
                fcf_cagr = None
            else:
                fcf_cagr = round(((final_fcf / initial_fcf) ** (1 / n_years) - 1) * 100, 2)

            return (fcf_yield, fcf_cagr, fcf_list)

        except Exception:
            return (None, None, [])


    # 2. Fallback: try yfinance
    result = try_yf(ticker)
    if result is not None and (
        result[0] is not None or result[1] is not None or (result[2] and len(result[2]) > 0)
    ):
        return result


    # 1. Try FMP first
    result = try_fmp(ticker, api_key)
    # FMP 결과가 모두 None/빈 리스트면 yfinance 시도
    if result is not None and (
        result[0] is not None or result[1] is not None or (result[2] and len(result[2]) > 0)
    ):
        return result

    return (None, None, [])  # Always return a tuple
    
def get_10yr_treasury_yield():
    try:
        tnx = yf.Ticker("^TNX")
        tnx_data = tnx.history(period="1d")
        latest_yield = tnx_data['Close'].iloc[-1]
        return round(latest_yield, 2)  # Already in percent
    except Exception as e:
        return f"Error fetching yield: {e}"


def dcf_valuation(fcf_history, discount_rate, long_term_growth, years=10, shares_outstanding=None, cagr = 0.05):
    
    if not fcf_history or len(fcf_history) < 2:
        return (None, None)

    start_fcf = fcf_history[0]  # oldest
    end_fcf = fcf_history[-1]   # most recent

    if start_fcf <= 0 or end_fcf <= 0:
        return (None, None)

    if discount_rate <= long_term_growth:
        return (None, None)  # Invalid terminal growth assumption

    if cagr is None or cagr <= 0:
        return (None, None)  # Invalid CAGR assumption
    est_cagr = cagr / 100.0 * 0.6 #conservative
    growth_rate = min(est_cagr, discount_rate)  # Ensure growth rate is reasonable

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

    return float(intrinsic_value), growth_rate * 100  # Return intrinsic value and growth rate in percentage


def get_trading_volume_vs_avg20(ticker_symbol: str) -> float:
    try:
        # Fetch 21 days of data
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="21d")

        if len(hist) < 21:
            return None  # Not enough data

        today_volume = hist["Volume"].iloc[-1]
        avg_volume_20 = hist["Volume"].iloc[:-1].mean()

        if avg_volume_20 == 0 or pd.isna(today_volume) or pd.isna(avg_volume_20):
            return None  # Invalid data

        # Return ratio (e.g., 1.5 means 150% of avg volume)
        return round(today_volume / avg_volume_20, 1)

    except Exception as e:
        print(f"[Error] {ticker_symbol}: {e}")
        return None



def has_stable_dividend_growth_cagr(ticker):
    try:
        stock = yf.Ticker(ticker)
        divs = stock.dividends

        if divs.empty:
            return None

        # Sum dividends annually
        annual_divs = divs.groupby(divs.index.year).sum()

        # Need at least 10 full years
        if len(annual_divs) < 10:
            return None

        # Get last full year (last year completed)
        last_year = dt.datetime.today().year - 1

        # Ensure we have dividends data up to last_year
        if last_year not in annual_divs.index:
            return None

        # Select exactly 10 years ending at last_year
        recent_years = sorted(annual_divs.index)
        recent_years = [year for year in recent_years if last_year - 9 <= year <= last_year]

        if len(recent_years) < 10:
            return None

        last_10_divs = [annual_divs[year] for year in recent_years]

        div_start = last_10_divs[0]
        div_end = last_10_divs[-1]

        # Validate data
        if div_start <= 0 or div_end <= 0:
            return None

        periods = len(last_10_divs) - 1  # 9 periods for 10 years

        cagr = (div_end / div_start) ** (1 / periods) - 1

        return cagr  # returns float (e.g., 0.05 for 5%)

    except Exception:
        return None

def has_stable_eps_growth_cagr(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        income_stmt = ticker_obj.financials  # Annual financials DataFrame

        if "Diluted EPS" not in income_stmt.index:
            return None

        eps_series = income_stmt.loc["Diluted EPS"].dropna()

        # Sort by date ascending (oldest to newest)
        eps_series = eps_series.sort_index()

        # Get current year to filter last 5 years
        current_year = dt.datetime.today().year

        # Filter EPS for last 5 years explicitly
        # income_stmt columns are timestamps, get their years
        eps_years = [col.year for col in eps_series.index]

        # Select only last 5 years (if available)
        selected_years = [year for year in eps_years if current_year - 5 <= year <= current_year - 1]

        # Filter eps_series to selected years only
        filtered_eps = eps_series[[col for col in eps_series.index if col.year in selected_years]]

        if len(filtered_eps) < 2:
            return None

        eps_list = filtered_eps.tolist()

        eps_start = eps_list[0]
        eps_end = eps_list[-1]

        if eps_start <= 0 or eps_end <= 0:
            tolerance = 0.95
            stable_growth = all(
                later >= earlier * tolerance for earlier, later in zip(eps_list, eps_list[1:])
            )
            return stable_growth

        periods = len(eps_list) - 1
        cagr = (eps_end / eps_start) ** (1 / periods) - 1

        return cagr

    except Exception:
        return None
    
# gets the most recent interest coverage ratio available
def get_interest_coverage_ratio(ticker):
    financials = yf.Ticker(ticker).financials # Annual financials, columns = dates (most recent first)
    ratio = None
    if not financials.columns.empty:
        for date in financials.columns:
            if date.year < dt.datetime.today().year - 5: # sift out old data
                return None

            try:
                ebit = financials.loc["Operating Income", date]
                interest_expense = financials.loc["Interest Expense", date]
                if math.isnan(interest_expense) or math.isnan(ebit) or not interest_expense or ebit is None or interest_expense is None:
                    continue # Avoid division by zero
                else:
                    ratio = round((ebit / abs(interest_expense)), 2)
                    break
            except KeyError:
                continue
        return ratio
    else:
        return None

def get_esg_score(ticker):
    ans = ''
    try:
        ticker_obj = yf.Ticker(ticker)
        esg = ticker_obj.sustainability
        if esg is None or esg.empty:
            return ''

        rateY = esg.loc['esgPerformance', 'esgScores']
        rateY_str = str(rateY).strip()
        ans = esg_dict.get(rateY_str, '')
    except Exception:
        ans = ''
    return ans


# def get_percentage_change(ticker):
#     ticker = yf.Ticker(ticker)

#     # Get last 2 days of price data
#     data = ticker.history(period="2d")

#     # Check if we have at least 2 days and prev_close is not zero
#     if len(data) >= 2:
#         prev_close = data['Close'].iloc[-2]
#         last_close = data['Close'].iloc[-1]

#         if prev_close != 0:
#             percent_change = ((last_close - prev_close) / prev_close) * 100
#             if percent_change >= 0:
#                 return (f" (+{percent_change:.2f}%)")  # e.g., (-6.20%)
#             else:
#                 return (f" ({percent_change:.2f}%)")  # e.g., (-6.20%)
#         else:
#             return ' ()'
#     else:
#         return ' ()'

### 1mo ver.
def get_percentage_change(ticker):
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


def download_industry_per():
    # FullRatio의 산업별 PER 페이지 URL
    url = 'https://fullratio.com/pe-ratio-by-industry'
    headers = {'User-Agent': 'Mozilla/5.0'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 테이블 찾기 (이때 table이 None인지 체크)
    table = soup.find('table')
    if table is None:
        raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

    # tbody가 있는 경우
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
    else:
        rows = table.find_all('tr')[1:] # 헤더 제외

    # 각 행에서 데이터 추출
    per_data = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 2:
            industry = cols[0].text.strip()
            pe_ratio = cols[1].text.strip()
            per_data.append({'Industry': industry, 'P/E Ratio': pe_ratio})

    # 결과 출력
    return pl.DataFrame(per_data)

def download_industry_roe():
    url_roe = 'https://fullratio.com/roe-by-industry'
    headers_roe = {'User-Agent': 'Mozilla/5.0'}

    response_roe = requests.get(url_roe, headers=headers_roe)
    soup_roe = BeautifulSoup(response_roe.text, 'html.parser')

    # 테이블 찾기 (이때 table이 None인지 체크)
    table_roe = soup_roe.find('table')
    if table_roe is None:
        raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

    # tbody가 있는 경우
    tbody_roe = table_roe.find('tbody')
    if tbody_roe:
        rows_roe = tbody_roe.find_all('tr')
    else:
        rows_roe = table_roe.find_all('tr')[1:] # 헤더 제외

    # 각 행에서 데이터 추출
    roe_data = []
    for row in rows_roe:
        cols_roe = row.find_all('td')
        if len(cols_roe) >= 2:
            industry_roe = cols_roe[0].text.strip()
            roe_num = cols_roe[1].text.strip()
            roe_data.append({'Industry': industry_roe, 'ROE': roe_num})

    # 결과 출력
    return pl.DataFrame(roe_data)


def download_industry_roa():
    url_roa = 'https://fullratio.com/roa-by-industry'
    headers_roa = {'User-Agent': 'Mozilla/5.0'}

    response_roa = requests.get(url_roa, headers=headers_roa)
    soup_roa = BeautifulSoup(response_roa.text, 'html.parser')

    # 테이블 찾기 (이때 table이 None인지 체크)
    table_roa = soup_roa.find('table')
    if table_roa is None:
        raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

    # tbody가 있는 경우
    tbody_roa = table_roa.find('tbody')
    if tbody_roa:
        rows_roa = tbody_roa.find_all('tr')
    else:
        rows_roa = table_roa.find_all('tr')[1:] # 헤더 제외

    # 각 행에서 데이터 추출
    roa_data = []
    for row in rows_roa:
        cols_roa = row.find_all('td')
        if len(cols_roa) >= 2:
            industry_roa = cols_roa[0].text.strip()
            roa_num = cols_roa[1].text.strip()
            roa_data.append({'Industry': industry_roa, 'ROA': roa_num})

    df_roa = pl.DataFrame(roa_data)
    return pl.DataFrame(roa_data)
#
df_per = download_industry_per()
df_roe = download_industry_roe()
df_roa = download_industry_roa()

def get_industry_per(ind, ticker):
    spy = yf.Ticker('SPY')
    spy_info = spy.info
    per = spy_info.get('trailingPE')
    try: 
        if ind is not None:
            ans = float(df_per.filter(pl.col('Industry') == ind).select("P/E Ratio").item())
            return ans
        return per
    except Exception:
        return per

def get_industry_roe(ind):
    try:
        if ind is not None:
            ans = float(df_roe.filter(pl.col('Industry') == ind).select("ROE").item())
            return ans/100.0
        else:
            return 0.08
    except Exception:
        return 0.08 

def get_industry_roa(ind):
    try:
        if ind is not None:
            ans = float(df_roa.filter(pl.col('Industry') == ind).select("ROA").item())
            return ans/100.0
        return 0.06
    except Exception:
        return 0.06

    
######## LOAD TICKERS ###########
raw_tickers = get_tickers(country, limit, sp500)

prohibited = {'AFA', 'BACRP', 'CDVM', 'NVL', 'TBB', 'TBC', 'VZA', "ANTM","SOJD","SOJE","SOJC","RY-PT","DUKB"} # no data on yfinance or frequently cause errors
def keep_ticker(t):
    return t not in prohibited
tickers = list(filter(keep_ticker, raw_tickers))


def ensure_cache_1y_for_tickers(tickers, cache_file="yf_cache_multi.csv"):
    import pandas as pd
    import yfinance as yf
    from datetime import datetime, timedelta

    today = pd.Timestamp((dt.datetime.today() - dt.timedelta(days = weekend)).date())
    one_year_ago = today - pd.Timedelta(days=365)

    # Load cache or create empty DataFrame
    if os.path.exists(cache_file):
        cache = pd.read_csv(cache_file, header=[0,1], index_col=0, parse_dates=True)
    else:
        cache = pd.DataFrame()

    # Find the first available business day >= one_year_ago
    if not cache.empty:
        available_dates = cache.index[cache.index >= one_year_ago]
        if len(available_dates) > 0:
            start_date = available_dates[0]
        else:
            start_date = today  # fallback, should not happen
    else:
        start_date = today - pd.tseries.offsets.BDay(252)  # fallback: 252 business days ago

    # For each ticker, check if 1y data exists; if not, download and append
    for ticker in tickers:
        need_download = False
        if cache.empty or (ticker, 'Close') not in cache.columns:
            need_download = True
        else:
            ticker_data = cache[(ticker, 'Close')]
            ticker_dates = ticker_data.dropna().index
            if not any((ticker_dates <= today) & (ticker_dates >= start_date)):
                need_download = True
            elif (ticker_dates < start_date).all():
                need_download = True

        if need_download:
            print(f"Downloading 1y data for {ticker}...")
            df_new = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=(today + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                                 interval="1d", auto_adjust=True, progress=False)
            if not df_new.empty:
                df_new = pd.concat({ticker: df_new}, axis=1)
                cache = pd.concat([cache, df_new])
                cache = cache[~cache.index.duplicated(keep='last')]
                cache = cache.sort_index()
                cache.to_csv(cache_file)
    return cache

# Usage before slicing:
cache = ensure_cache_1y_for_tickers(tickers, cache_file="yf_cache_multi.csv")

# Now, get the first available business day >= 1y ago for slicing
one_year_ago = pd.Timestamp(datetime.today().date()) - pd.Timedelta(days=365)
available_dates = cache.index[cache.index >= one_year_ago]
if len(available_dates) > 0:
    start_date = available_dates[0]
else:
    start_date = cache.index[0]  # fallback

end_date = pd.Timestamp((dt.datetime.today() - dt.timedelta(days = weekend)).date())
cache = cache.loc[start_date:end_date]
def append_missing_to_cache_up_to_today(tickers, cache_file="yf_cache_multi.csv"):

    today = pd.Timestamp.today().normalize()

    if os.path.exists(cache_file):
        cache = pd.read_csv(cache_file, header=[0, 1], index_col=0, parse_dates=True)
    else:
        cache = pd.DataFrame()

    updated = False

    for ticker in tickers:
        # Determine last date in cache
        if not cache.empty and (ticker, 'Close') in cache.columns:
            last_date = cache[(ticker, 'Close')].dropna().index.max()
            start_date = last_date + pd.Timedelta(days=1)
        else:
            start_date = today - pd.Timedelta(days=365)

        if start_date > today:
            print(f"{ticker}: Already up to date.")
            continue

        print(f"{ticker}: Downloading from {start_date.date()} to {today.date()}...")

        df_new = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=(today + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if not df_new.empty:
            # Wrap columns in MultiIndex only if not already
            if not isinstance(df_new.columns, pd.MultiIndex):
                df_new.columns = pd.MultiIndex.from_product([[ticker], df_new.columns])
            else:
                # If it's already multi-indexed, just proceed
                pass

            cache = pd.concat([cache, df_new])
            updated = True
        else:
            print(f"{ticker}: No new data.")

    if updated:
        cache = cache[~cache.index.duplicated(keep='last')]
        cache = cache.sort_index()
        cache.to_csv(cache_file)
        print("✅ Cache updated.")
    else:
        print("✅ All tickers already up to date.")

    return cache


append_missing_to_cache_up_to_today(tickers)

# 캐시 파일에서 1년치 데이터 불러오기
cache_file = "yf_cache_multi.csv"
cache = pd.read_csv(cache_file, header=[0,1], index_col=0, parse_dates=True)

# 오늘 날짜와 1년 전 날짜 계산
end_date = dt.datetime.today() - dt.timedelta(days = weekend)
start_date = end_date - dt.timedelta(days=365)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

# 날짜 범위로 슬라이싱 (더 견고하게)
cache = cache[(cache.index >= pd.Timestamp(start_date)) & (cache.index <= pd.Timestamp(end_date))]

# 안전하게 'Close' 데이터만 추출
if isinstance(cache.columns, pd.MultiIndex):
    close_columns = [col for col in cache.columns if col[1] == 'Close']
    df_momentum = cache[close_columns]
    df_momentum.columns = [col[0] for col in df_momentum.columns]  # 티커명만 남김
else:
    df_momentum = cache[['Close']]
    df_momentum.columns = [tickers[0]]

def check_momentum_conditions(ticker: str) -> dict:
    result = {
        'ma_crossover': False,
        'ma_crossover_lt': False,
        'return_20d': False,
        'return_60d': False,
        'rsi_rebound': False,
        'macd_golden_cross': False
    }

    try:
        # 티커가 데이터에 없으면 바로 반환
        if ticker not in df_momentum.columns:
            print(f"[Error] {ticker} not in df_momentum.columns")
            return result

        # 개별 종목 시계열 추출 후 'Close'로 컬럼명 통일
        df_ticker = df_momentum[[ticker]].copy()
        df_ticker.columns = ['Close']

        # 결측치 처리
        df_ticker['Close'] = df_ticker['Close'].ffill()

        if df_ticker['Close'].isna().all():
            print(f"[Error] All 'Close' values are NaN for {ticker}")
            return result

        if len(df_ticker) < 22:
            print(f"[Warning] Not enough data rows for 20-day return calculation for {ticker} (rows={len(df_ticker)})")
            return result

        # 이동평균선 계산
        df_ticker['MA20'] = df_ticker['Close'].rolling(window=5).mean()
        df_ticker['MA60'] = df_ticker['Close'].rolling(window=20).mean()

        if pd.notna(df_ticker['MA20'].iloc[-1]) and pd.notna(df_ticker['MA60'].iloc[-1]):
            if df_ticker['MA20'].iloc[-1] > df_ticker['MA60'].iloc[-1]:
                result['ma_crossover'] = True

        df_ticker['MA50'] = df_ticker['Close'].rolling(window=50).mean()
        df_ticker['MA200'] = df_ticker['Close'].rolling(window=200).mean()

        if pd.notna(df_ticker['MA50'].iloc[-1]) and pd.notna(df_ticker['MA200'].iloc[-1]):
            if df_ticker['MA50'].iloc[-1] > df_ticker['MA200'].iloc[-1]:
                result['ma_crossover_lt'] = True

        # 20일 수익률 계산
        try:
            return_20d = (df_ticker['Close'].iloc[-1] / df_ticker['Close'].iloc[-21] - 1) * 100
            if return_20d >= 10:
                result['return_20d'] = True
        except IndexError:
            print(f"[Warning] Not enough data for 20-day return calculation for {ticker}")

        # 60일 수익률 계산
        try:
            return_60d = (df_ticker['Close'].iloc[-1] / df_ticker['Close'].iloc[-61] - 1) * 100
            if return_60d >= 10:
                result['return_60d'] = True
        except IndexError:
            print(f"[Warning] Not enough data for 60-day return calculation for {ticker}")

        # RSI
        try:
            rsi = ta.momentum.RSIIndicator(df_ticker['Close'], window=14).rsi()
            if len(rsi) >= 7:
                recent = rsi.iloc[-7:]
                if all(recent > 50) and recent.iloc[-1] < 70 and recent.is_monotonic_increasing:
                    result['rsi_rebound'] = True
        except Exception as e:
            print(f"[RSI Error] {ticker}: {e}")

        # MACD
        try:
            macd_obj = ta.trend.MACD(df_ticker['Close'])
            macd_line = macd_obj.macd()
            signal_line = macd_obj.macd_signal()

            if len(macd_line) >= 7:
                macd_recent = macd_line.iloc[-7:]
                signal_recent = signal_line.iloc[-7:]
                if (macd_recent > signal_recent).sum() >= 5 and macd_recent.iloc[-1] > signal_recent.iloc[-1]:
                    if macd_recent.iloc[-1] > macd_recent.iloc[0]:
                        result['macd_golden_cross'] = True
        except Exception as e:
            print(f"[MACD Error] {ticker}: {e}")

    except Exception as e:
        print(f"[Download Error] Ticker {ticker}: {e}")

    return result


def check_momentum_conditions_batch(tickers: list) -> pd.DataFrame:
    results = []
    for ticker in tickers:
        # print(f"Processing {ticker} ...")
        res = check_momentum_conditions(ticker)
        res['Ticker'] = ticker
        results.append(res)
    # 결과 리스트를 DataFrame으로 변환 (Ticker 컬럼 첫 칼럼으로 이동)
    df_results = pd.DataFrame(results)
    cols = ['Ticker'] + [c for c in df_results.columns if c != 'Ticker']
    df_results = df_results[cols]
    return df_results

df_batch_result = check_momentum_conditions_batch(tickers)

def score_momentum(ma, ma_lt, ret, ret60, rsi, macd):
    score = 0
    if ma:
        score += 10
    if ma_lt:
        score += 20
    if ret:
        score += 10
    if ret60:
        score += 20
    if rsi:
        score += 20
    if macd:
        score += 20
    return score

def get_operating_income_yoy(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        financials = ticker_obj.financials

        # Check if 'Operating Income' is in the DataFrame
        if "Operating Income" not in financials.index:
            return None

        # Extract and clean
        operating_income = financials.loc["Operating Income"].dropna()

        # Ensure enough data and sort oldest to newest
        if len(operating_income) < 3:
            return None

        income_values = operating_income[::-1].values.tolist()

        # Check if non-decreasing
        if all(later >= earlier for earlier, later in zip(income_values, income_values[1:])):
            return True

        oi_start = income_values[0]
        oi_end = income_values[-1]

        # Check for valid values
        if oi_start is None or oi_end is None or oi_start <= 0 or oi_end <= 0:
            return False

        periods = len(income_values) - 1
        cagr = (oi_end / oi_start) ** (1 / periods) - 1

        return cagr

    except Exception as e:
        print(f"[Error processing {ticker}]: {e}")
        return None

def get_operating_income_qoq(ticker):
    try:
        ticker_obj = yf.Ticker(ticker)
        financials = ticker_obj.quarterly_financials

        # Check if 'Operating Income' exists
        if "Operating Income" not in financials.index:
            return None

        # Drop NaNs and sort from oldest to newest
        operating_income = financials.loc["Operating Income"].dropna()[::-1]

        if len(operating_income) < 3:
            return None

        income_values = operating_income.values.tolist()

        # Check for strictly non-decreasing trend
        if all(later >= earlier for earlier, later in zip(income_values, income_values[1:])):
            return True

        oi_start = income_values[0]
        oi_end = income_values[-1]

        # Validate for meaningful CAGR
        if oi_start is None or oi_end is None or oi_start <= 0 or oi_end <= 0:
            return False

        periods = len(income_values) - 1  # number of quarters
        qoq_cagr = (oi_end / oi_start) ** (1 / periods) - 1

        return qoq_cagr

    except Exception as e:
        print(f"[Error processing {ticker}]: {e}")
        return None
    
def score_intrinsic_value(conf_lower, conf_upper, current_price, fcf_yield, tenyr_treasury_yield, fcf_cagr):
    score = 0

    if conf_lower is not None and conf_upper is not None and current_price is not None:
        if conf_lower <= current_price <= conf_upper:
            score += 2  # price is within fair value range
        else:
            score -= 1  # price outside fair value range

    if fcf_yield is not None:
        if fcf_yield > tenyr_treasury_yield:
            score += 2
        elif fcf_yield < tenyr_treasury_yield:
            score -= 1

    if fcf_cagr is not None:
        if fcf_cagr >= 0:
            score += 2
        else:
            score -= 1

    return score


def monte_carlo_dcf_valuation(
    ticker,
    initial_fcf,
    wacc,
    terminal_growth_rate,
    projection_years=5,
    num_simulations=10_000,
):
    if initial_fcf <= 0:
        return (None, None)
    if wacc <= terminal_growth_rate:
        return (None, None)

    if projection_years <= 0 or num_simulations <= 0:
        return (None, None)

    stock = yf.Ticker(ticker)
    info = stock.info

    shares_outstanding = info.get('sharesOutstanding')
    if not shares_outstanding or shares_outstanding <= 0:
        return (None, None)


    total_debt = info.get('totalDebt') or 0
    cash = info.get('totalCash') or 0
    net_debt = total_debt - cash

    growth_mean = 0.08
    growth_std = 0.03

    equity_values = []

    for _ in range(num_simulations):
        fcf = initial_fcf
        total_value = 0

        for year in range(1, projection_years + 1):
            growth_rate = np.random.normal(growth_mean, growth_std)
            fcf *= (1 + growth_rate)
            discounted_fcf = fcf / ((1 + wacc) ** year)
            total_value += discounted_fcf

        terminal_value = fcf * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)
        discounted_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

        enterprise_value = total_value + discounted_terminal_value
        equity_value = enterprise_value - net_debt

        equity_values.append(equity_value)

    equity_values = np.array(equity_values)
    fair_value_per_share = equity_values / shares_outstanding

    # mean_val = np.mean(fair_value_per_share)
    # median_val = np.median(fair_value_per_share)
    # std_val = np.std(fair_value_per_share)
    conf_lower = np.percentile(fair_value_per_share, 2.5)
    conf_upper = np.percentile(fair_value_per_share, 97.5)

    return (float(conf_lower), float(conf_upper))

def classify_cyclicality(industry):
    """
    Classify a ticker as 'cyclical', 'defensive', or 'neutral' based on its industry.

    Returns:
      - 'cyclical' if industry matches cyclical keywords
      - 'defensive' if industry matches defensive keywords
      - 'neutral' if no clear match
      - None if industry info unavailable or error
    """

    cyclical_keywords = [
    "auto", "apparel", "footwear", "home improvement", "internet retail", "leisure", "lodging",
    "restaurant", "specialty retail", "textile", "travel", "coal", "oil", "gas", "renewable",
    "asset management", "bank", "capital markets", "credit services", "insurance",
    "mortgage", "real estate", "aerospace", "defense", "air freight", "airline",
    "building", "conglomerate", "construction", "electrical equipment", "engineering",
    "industrial", "machinery", "marine", "railroad", "waste", "chemical", "container",
    "metal", "paper", "advertising", "broadcasting", "cable", "casino", "communication",
    "gaming", "interactive media", "movies", "publishing", "radio", "recreational",
    "software", "semiconductor", "information technology", "it services"
    ]


    defensive_keywords = [
    "beverages", "confectioner", "food", "household", "packaged", "personal product",
    "tobacco", "biotech", "healthcare", "health", "medical device", "pharma",
    "utility", "power producer", "utilities", 
    ]

    try:
        if not industry:
            return None  # No industry info

        industry_lower = industry.lower()

        # Check cyclical
        for kw in cyclical_keywords:
            if kw in industry_lower:
                return "cyclical"

        # Check defensive
        for kw in defensive_keywords:
            if kw in industry_lower:
                return "defensive"

        # If no matches, neutral
        return "neutral"

    except Exception as e:
        return None
    
retried_once = set()
q = Queue()
for ticker in tickers:
    q.put(ticker)

# with shelve.open("cache/ticker_cache") as cache:
#     # Clear all the cache entries by deleting the keys
#     cache.clear()

def process_ticker_quantitatives():
    while not q.empty():
        ticker = q.get()
        try:

            info = yf.Ticker(ticker).info
            beta = info.get("beta", None)
            name = info.get("shortName", ticker)
            industry = info.get("industry", None)
            currentPrice = info.get("currentPrice", None)
            percentage_change = get_percentage_change(ticker)
            debtToEquity = info.get('debtToEquity', None) # < 0.5
            debtToEquity = debtToEquity/100 if debtToEquity is not None else None
            currentRatio = info.get('currentRatio', None) # 초점: 회사의 단기 유동성, > 1.5 && < 2.5
            shares_outstanding = info.get('sharesOutstanding')
            pbr = info.get('priceToBook', None) # 초점: 자산가치, 저pbr종목은 저평가된 자산 가치주로 간주. 장기 수익률 설명력 높음 < 1.5 (=being traded at 1.5 times its book value (asset-liab))
            per = info.get('trailingPE', None) # 초점: 수익성, over/undervalue? 저per 종목 선별, 10-20전후(혹은 산업평균)로 낮고 높음 구분. 주가가 그 기업의 이익에 비해 과대/과소평가되어 있다는 의미
                                                                       # low per could be undervalued or company in trouble, IT, 바이오 등 성장산업은 자연스레 per이 높게 형성
                                                                             # low per could be undervalued or company in trouble, IT, 바이오 등 성장산업은 자연스레 per이 높게 형성
            industry_per = get_industry_per(industry, ticker)
            industry_per = round(industry_per) if industry_per is not None else industry_per
            industry_roe = get_industry_roe(industry)
            industry_roa = get_industry_roa(industry)

            roe = info.get('returnOnEquity', None) # 수익성 높은 기업 선별. 고roe + 저pbr 조합은 가장 유명한 퀀트 전략. > 8% (0.08) 주주 입장에서 수익성
            roa = info.get('returnOnAssets', None) # > 6% (0.06), 기업 전체 효율성
            #ROE가 높고 ROA는 낮다면? → 부채를 많이 이용해 수익을 낸 기업일 수 있음. ROE와 ROA 모두 높다면? → 자산과 자본 모두 효율적으로 잘 운용하고 있다는 의미.
            #A = L + E
            
            icr = get_interest_coverage_ratio(ticker)
            eps_growth = has_stable_eps_growth_cagr(ticker) # earnings per share, the higher the better, buffett looks for stable EPS growth
            # eps_growth_quart = has_stable_eps_growth_quarterly(ticker) 
            div_growth = has_stable_dividend_growth_cagr(ticker) # buffett looks for stable dividend growth for at least 10 years
            # bvps_growth = bvps_undervalued(info.get('bookValue', None), currentPrice)
            
            operating_income_yoy = get_operating_income_yoy(ticker)
            operating_income_qoq = get_operating_income_qoq(ticker)
            
            ma = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'ma_crossover'].values[0]
            ma_lt = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'ma_crossover_lt'].values[0]
            ret20 = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'return_20d'].values[0]
            ret60 = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'return_60d'].values[0]
            rsi = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'rsi_rebound'].values[0]
            macd = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'macd_golden_cross'].values[0]

            momentum_score = score_momentum(ma, ma_lt, ret20, ret60, rsi, macd)
            # vol = get_trading_volume_vs_avg20(ticker)
            esg = get_esg_score(ticker)
        
            quantitative_buffett_score = buffett_score(debtToEquity, currentRatio, pbr, per, industry_per, roe, industry_roe, roa, industry_roa, eps_growth, div_growth, icr, operating_income_yoy, operating_income_qoq)
            fcf_yield, fcf_cagr, fcf_list = get_fcf_yield_and_cagr(ticker, api_key=fmp_key)
            tenyr_treasury_yield = get_10yr_treasury_yield()
            discount_rate = (tenyr_treasury_yield+(beta*5.0))/100.0 if beta is not None else (tenyr_treasury_yield+5.0)/100.0
            terminal_growth_rate = 0.02 #0.03
            # intrinsic_value, est_fcf_cagr = dcf_valuation(fcf_list, discount_rate=discount_rate, long_term_growth=terminal_growth_rate, years=10, shares_outstanding=shares_outstanding, cagr=fcf_cagr)
            if not fcf_list or fcf_list[-1] is None:
                # handle missing FCF, e.g. skip, default, or raise error
                initial_fcf = None
            else:
                initial_fcf = fcf_list[-1]

            if initial_fcf is None:
                # maybe skip valuation or set a default score
                intrinsic_value_range = (None, None)
            else:
                intrinsic_value_range = monte_carlo_dcf_valuation(
                    ticker, initial_fcf, discount_rate, terminal_growth_rate, projection_years=5, num_simulations=10_000
                )
            
            
            intrinsic_value_score = score_intrinsic_value(*intrinsic_value_range, currentPrice, fcf_yield, tenyr_treasury_yield, fcf_cagr)
            quantitative_buffett_score += intrinsic_value_score
            
            

            ## FOR extra 10 score:::
            # MOAT -> sustainable competitive advantage that protects a company from its competitors, little to no competition, dominant market share, customer loyalty 
            # KEY: sustainable && long-term durability
            # ex) brand power(Coca-Cola), network effect(Facebook, Visa), cost advantage(Walmart, Costco), high switching costs(Adobe),
            # regulatory advantage(gov protection), patients(Pfizer, Intel)
            
            roe_print = f'{round(roe*100,1)}%' if roe is not None else 'N/A'
            roe_print += f'({round(industry_roe*100)})' if industry_roe is not None else ''

            roa_print = f'{round(roa*100,1)}%' if roa is not None else 'N/A'
            roa_print += f'({round(industry_roa*100)})' if industry_roe is not None else ''

            per_print = f'{round(per,2)}' if per is not None else 'N/A'
            per_print += f'({industry_per})' if industry_per is not None else ''

            operating_income_yoy = f'{operating_income_yoy:.0%}' if isinstance(operating_income_yoy, float) else operating_income_yoy
            operating_income_qoq = f'{operating_income_qoq:.0%}' if isinstance(operating_income_qoq, float) else operating_income_qoq

            result = {
                "티커": ticker,
                "종목": name,
                "B-Score": round(quantitative_buffett_score, 1),
                "업종": industry,
                "주가(1개월대비)": f"${currentPrice:,.2f}" + percentage_change,
                "추정DCF": (f"{intrinsic_value_range[0]:,.0f} - {intrinsic_value_range[1]:,.0f}" if intrinsic_value_range and intrinsic_value_range != (None, None) else 'N/A'),
                "부채비율": round(debtToEquity, 2) if debtToEquity is not None else 'N/A',
                "유동비율": round(currentRatio, 2) if currentRatio is not None else 'N/A',
                "PBR": round(pbr,2) if pbr is not None else None,
                "PER(업종)": per_print,
                "ROE(업종)": roe_print,
                "ROA(업종)": roa_print,
                "ICR": round(icr,1) if icr is not None else 'N/A',
                "FCF수익률": f"{fcf_yield:.1f}%" if fcf_yield is not None else 'N/A',
                "FCF성장률": f"{fcf_cagr:.1f}%" if fcf_cagr is not None else 'N/A',
                "EPS성장률": eps_growth if isinstance(eps_growth, bool) else (f"{eps_growth:.2%}" if eps_growth is not None else 'N/A'), #use this instead of operating income incrs for quart/annual 
                "배당성장률": div_growth if isinstance(div_growth, bool) else (f"{div_growth:.2%}" if div_growth is not None else 'N/A'),
                "영업이익률(Y/Q)": str(operating_income_yoy if operating_income_yoy is not None else 'N/A') + '/' + str(operating_income_qoq if operating_income_qoq is not None else 'N/A'),
                '모멘텀': momentum_score,
                # '거래량': vol,
                'ESG': esg, #works only for US stocks
            }

            with data_lock:
                data.append(result)

        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            with data_lock:
                if ticker not in retried_once:
                    retried_once.add(ticker)
                    q.put(ticker)
            if "429" in str(e):
                print("Too many requests! Waiting 10 seconds...")
                time.sleep(10)
        
        finally:
            q.task_done()
            #time.sleep(2)
    

threads = []

for _ in range(NUM_THREADS):
    t = threading.Thread(target=process_ticker_quantitatives)
    t.start()
    threads.append(t)

for t in threads:
    t.join()

q.join()

df = pd.DataFrame(data)
# df.dropna(subset=["D/E", "CR", "P/B", "ROE", "ROA", "PER", "ICR"], inplace = True)

min_b_score = df["B-Score"].min()
max_b_score = df["B-Score"].max()

if min_b_score == max_b_score:
    df["B-Score"] = 0
else:
    df["B-Score"] = (df["B-Score"] - min_b_score) / (max_b_score - min_b_score) * 100

df["B-Score"] = df["B-Score"].round(0)


# 모멘텀 정규화 및 반올림
max_momentum = df["모멘텀"].max()
df["모멘텀"] = (df["모멘텀"] / max_momentum) * 100
df["모멘텀"] = df["모멘텀"].round(0)

df["합계점수"] = df["B-Score"] + df["모멘텀"]

df = df.sort_values(by='합계점수', ascending=False)

# 상위 X개 티커 리스트 추출
top_tickers = df['티커'].head(opt).tolist()
top_tickers_news = df['티커'].tolist()

#################################################################
def get_news_for_tickers(tickers, api_token):
    all_news = []

    for ticker in tickers:
        try:
            company_info = yf.Ticker(ticker).info
            full_name = company_info.get("shortName", "")
        except Exception as e:
            print(f"[{ticker}] ⚠️ Failed to retrieve company info: {e}")
            continue

        if not full_name:
            print(f"[{ticker}] ⚠️ No company name found, skipping.")
            continue

        published_after = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        url = "https://api.marketaux.com/v1/news/all"
        params = {
            "api_token": api_token,
            "symbols": ticker.upper(),
            "language": "en",
            "published_after": published_after,
            "limit": 5,  # Fetch extra to allow filtering
            "sort": "relevance",
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            articles = response.json().get("data", [])
        except Exception as e:
            print(f"[{ticker}] ❌ API request failed: {e}")
            continue

        filtered_articles = []

        for article in articles:
            relevant = False
            sentiment_score = None

            for entity in article.get("entities", []):
                if entity.get("symbol", "").upper() == ticker.upper():
                    relevant = True
                    score = entity.get("sentiment_score")
                    try:
                        sentiment_score = round(float(score), 2)
                    except (TypeError, ValueError):
                        sentiment_score = None
                    break

            if not relevant:
                continue

            filtered_articles.append({
                "기업명": full_name,
                "기사 제목": article.get("title"),
                "감정지수": sentiment_score,
                "뉴스 요약": article.get("description"),
                "발행일": article.get("published_at", "")[:10],
                "URL": article.get("url"),
            })

            if len(filtered_articles) >= 3:
                break

        if filtered_articles:
            all_news.extend(filtered_articles)
        else:
            print(f"[{ticker}] ℹ️ No relevant news articles found.")

    return pd.DataFrame(all_news)
#################################################################
news_df = get_news_for_tickers(top_tickers_news, api_token=marketaux_api)
#################################################################

# Seleccionar Criterio de Optimización
optimization_criterion = 'sortino'  # Cambia a 'sharpe', 'cvar', 'sortino' o 'variance' para optimizar esos criterios

symbols = top_tickers

# 오늘 날짜
end_date = dt.datetime.today() - dt.timedelta(days = weekend)

# 1년 전 날짜 (365일 전)
start_date = end_date - timedelta(days=365)

# 문자열 포맷으로 변환 (yfinance에 맞게)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

# 'Close' 가격만 추출 (안전성 보강)
if isinstance(cache.columns, pd.MultiIndex):
    # 'Close'가 있는 컬럼만 추출
    close_columns = [col for col in cache.columns if col[1] == 'Close']
    close_df = cache[close_columns]
    close_df.columns = [col[0] for col in close_df.columns]  # 티커명만 남김
else:
    if 'Close' in cache.columns:
        close_df = cache[['Close']]
        close_df.columns = [tickers[0]] if 'tickers' in locals() and tickers else ['Close']
    else:
        raise ValueError("No 'Close' column found in single-index DataFrame.")

# 상위 티커만 선택
symbols_in_data = [s for s in symbols if s in close_df.columns]
if not symbols_in_data:
    raise ValueError("No symbols found in cached data.")

data = close_df[symbols_in_data]

returns = data.pct_change(fill_method='pad').dropna()

# Sharpe Ratio 최적화 함수
def objective_sharpe(weights): 
    port_return = np.dot(weights, returns.mean()) * 252
    port_vol = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    return -port_return / port_vol  # 최대화 위해 음수

# CVaR 최적화 함수 (5% VaR 기준)
def objective_cvar(weights):
    portfolio_returns = returns.dot(weights)  # 수정: np.dot(returns, weights)도 가능하지만 DataFrame이면 .dot이 더 안전
    alpha = 0.05
    var = np.percentile(portfolio_returns, 100 * alpha)
    cvar = portfolio_returns[portfolio_returns <= var].mean()
    return cvar  # minimize에서 최소화(손실 최대화) → 부호 바꿔야 함
    # return -cvar  # CVaR 최대화하려면 음수로 반환

# Sortino Ratio 최적화 함수
def objective_sortino(weights):
    portfolio_returns = returns.dot(weights)  # 수정: np.dot(weights) → returns.dot(weights)
    mean_return = portfolio_returns.mean() * 252
    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    if downside_std == 0:
        return 0  # 또는 큰 값 반환
    sortino_ratio = mean_return / downside_std
    return -sortino_ratio  # 최대화 위해 음수

# 분산 최소화 함수
def objective_variance(weights):
    return np.dot(weights.T, np.dot(returns.cov() * 252, weights))

# Las restricciones
cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

# Los límites para los pesos
bounds = tuple((0, 1) for x in range(len(symbols)))


# Optimización
init_guess = np.array(len(symbols) * [1. / len(symbols),])
if optimization_criterion == 'sharpe':
    opt_results = minimize(objective_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'cvar':
    opt_results = minimize(objective_cvar, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'sortino':
    opt_results = minimize(objective_sortino, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
elif optimization_criterion == 'variance':
    opt_results = minimize(objective_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons)

# Los pesos óptimos
optimal_weights = opt_results.x


# Optimizar todos los criterios
opt_results_cvar = minimize(objective_cvar, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_sortino = minimize(objective_sortino, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_variance = minimize(objective_variance, init_guess, method='SLSQP', bounds=bounds, constraints=cons)
opt_results_sharpe = minimize(objective_sharpe, init_guess, method='SLSQP', bounds=bounds, constraints=cons)

# Pesos óptimos para cada criterio
optimal_weights_cvar = opt_results_cvar.x
optimal_weights_sortino = opt_results_sortino.x
optimal_weights_variance = opt_results_variance.x
optimal_weights_sharpe = opt_results_sharpe.x

# Graficar la frontera eficiente
port_returns = []
port_volatility = []
sharpe_ratio = []
all_weights = []  # almacena los pesos de todas las carteras simuladas

num_assets = len(symbols)
num_portfolios = 50000

np.random.seed(101)

for single_portfolio in range(num_portfolios):
    weights = np.random.random(num_assets)
    weights /= np.sum(weights)
    returns_portfolio = np.dot(weights, returns.mean()) * 252
    volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
    sr = returns_portfolio / volatility
    sharpe_ratio.append(sr)
    port_returns.append(returns_portfolio)
    port_volatility.append(volatility)
    all_weights.append(weights)  # registra los pesos para esta cartera

plt.figure(figsize=(12, 8))
plt.scatter(port_volatility, port_returns, c=sharpe_ratio, cmap='viridis')
plt.colorbar(label='Sharpe Ratio')
plt.xlabel('Volatility')
plt.ylabel('Return')

# Calcular y graficar los retornos y la volatilidad del portafolio óptimo para cada criterio
opt_returns_cvar = np.dot(optimal_weights_cvar, returns.mean()) * 252
opt_volatility_cvar = np.sqrt(np.dot(optimal_weights_cvar.T, np.dot(returns.cov() * 252, optimal_weights_cvar)))
opt_portfolio_cvar = plt.scatter(opt_volatility_cvar, opt_returns_cvar, color='hotpink', s=50, label='CVaR')

opt_returns_sortino = np.dot(optimal_weights_sortino, returns.mean()) * 252
opt_volatility_sortino = np.sqrt(np.dot(optimal_weights_sortino.T, np.dot(returns.cov() * 252, optimal_weights_sortino)))
opt_portfolio_sortino = plt.scatter(opt_volatility_sortino, opt_returns_sortino, color='g', s=50, label='Sortino')

opt_returns_variance = np.dot(optimal_weights_variance, returns.mean()) * 252
opt_volatility_variance = np.sqrt(np.dot(optimal_weights_variance.T, np.dot(returns.cov() * 252, optimal_weights_variance)))
opt_portfolio_variance = plt.scatter(opt_volatility_variance, opt_returns_variance, color='b', s=50, label='Variance')

opt_returns_sharpe = np.dot(optimal_weights_sharpe, returns.mean()) * 252
opt_volatility_sharpe = np.sqrt(np.dot(optimal_weights_sharpe.T, np.dot(returns.cov() * 252, optimal_weights_sharpe)))
opt_portfolio_sharpe = plt.scatter(opt_volatility_sharpe, opt_returns_sharpe, color='r', s=50, label='Sharpe')

plt.legend(loc='upper right')

plt.show()


# Función para calcular el drawdown máximo
def max_drawdown(return_series):
    comp_ret = (1 + return_series).cumprod()
    peak = comp_ret.expanding(min_periods=1).max()
    dd = (comp_ret/peak) - 1
    return dd.min()

def detailed_portfolio_statistics(weights):
    portfolio_returns = returns.dot(weights)
    mean_return_annualized = gmean(portfolio_returns + 1)**252 - 1
    std_dev_annualized = portfolio_returns.std() * np.sqrt(252)
    skewness = skew(portfolio_returns)
    kurt = kurtosis(portfolio_returns)
    max_dd = max_drawdown(portfolio_returns)
    count = len(portfolio_returns)
    tnx = yf.Ticker("^TNX")
    tnx_data = tnx.history(period="1d")
    latest_yield = tnx_data['Close'].iloc[-1]
    risk_free_rate = round(latest_yield/100.0, 2)
    sharpe_ratio = (mean_return_annualized - risk_free_rate) / std_dev_annualized

    # CVaR 계산 (5% 수준)
    alpha = 0.05
    sorted_returns = np.sort(portfolio_returns)
    var_index = int(np.floor(alpha * len(sorted_returns)))
    var = sorted_returns[var_index]
    cvar = sorted_returns[:var_index].mean()
    # 연율화
    cvar_annualized = (1 + cvar) ** 252 - 1

    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_std_dev = downside_returns.std() * np.sqrt(252)
    sortino_ratio = mean_return_annualized / downside_std_dev if downside_std_dev != 0 else np.nan
    variance = std_dev_annualized ** 2 
    
    return mean_return_annualized, std_dev_annualized, skewness, kurt, max_dd, count, sharpe_ratio, cvar_annualized, sortino_ratio, variance
# Calcular estadísticas para cada portafolio
statistics_cvar = detailed_portfolio_statistics(optimal_weights_cvar)
statistics_sortino = detailed_portfolio_statistics(optimal_weights_sortino)
statistics_variance = detailed_portfolio_statistics(optimal_weights_variance)
statistics_sharpe = detailed_portfolio_statistics(optimal_weights_sharpe)

# Nombres de las estadísticas
statistics_names = ['Retorno anualizado', 'Volatilidad anualizada', 'Skewness', 'Kurtosis', 'Max Drawdown', 'Conteo de datos', 'Sharpe Ratio', 'CVaR', 'Ratio Sortino', 'Varianza']

# Diccionario que asocia los nombres de los métodos de optimización con los pesos óptimos y las estadísticas
portfolio_data = {
    'CVaR': {
        'weights': optimal_weights_cvar,
        'statistics': detailed_portfolio_statistics(optimal_weights_cvar)
    },
    'Sortino': {
        'weights': optimal_weights_sortino,
        'statistics': detailed_portfolio_statistics(optimal_weights_sortino)
    },
    'Variance': {
        'weights': optimal_weights_variance,
        'statistics': detailed_portfolio_statistics(optimal_weights_variance)
    },
    'Sharpe': {
        'weights': optimal_weights_sharpe,
        'statistics': detailed_portfolio_statistics(optimal_weights_sharpe)
    },
}

# 1. 포트폴리오 비중 표 (각 방법별, 티커별 비중)
weight_rows = []
for method, data in portfolio_data.items():
    for symbol, weight in zip(symbols, data['weights']):
        weight_rows.append({
            '최적화 기준': method,
            '티커': symbol,
            '비중(%)': round(weight * 100, 2)
        })
df_weights = pd.DataFrame(weight_rows)

# 2. 포트폴리오 통계 표 (각 방법별 통계 한 줄)
statistics_names_kr = [
    '연환산 수익률', '연환산 변동성', '왜도', '첨도', '최대 낙폭', '데이터 개수',
    '샤프 비율', 'CVaR', '소르티노 비율', '분산'
]
stats_rows = []
for method, data in portfolio_data.items():
    stats_dict = {'최적화 기준': method}
    for name_kr, stat in zip(statistics_names_kr, data['statistics']):
        # 숫자는 모두 소수점 둘째자리로 반올림, 데이터 개수는 정수로
        if name_kr == '데이터 개수':
            stats_dict[name_kr] = int(stat)
        else:
            stats_dict[name_kr] = np.round(stat, 2)
    stats_rows.append(stats_dict)
df_stats = pd.DataFrame(stats_rows)

filename = f"result_{country}_{formattedDate}.xlsx"

def autofit_columns_and_wrap(ws, df: pd.DataFrame, workbook):
    # 픽셀 -> 문자 수 환산 (0.1428 배율 기준)
    pixel_widths = [92, 200, 50, 500, 85, 150]
    char_widths = [round(p * 0.1428) for p in pixel_widths]

    # wrap + top-align 포맷
    wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})

    # 헤더 작성 및 열 너비 설정
    for i, col in enumerate(df.columns):
        width = char_widths[i] if i < len(char_widths) else 20
        ws.set_column(i, i, width)
        ws.write(0, i, str(col), wrap_format)

    # 데이터 셀 작성
    for row in range(1, len(df) + 1):
        for col in range(len(df.columns)):
            val = df.iat[row - 1, col]

            # NaN / inf / None -> 문자열 변환
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    val = str(val)
            elif val is None:
                val = ""

            # Excel 쓰기 실패 대비 안전 write
            try:
                ws.write(row, col, val, wrap_format)
            except Exception:
                ws.write(row, col, str(val), wrap_format)


with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:

      # 종목분석 시트 먼저 생성해야 함
    df.to_excel(writer, index=False, sheet_name='종목분석')  # df_analysis는 종목분석 데이터프레임

    # 기존 포트폴리오비중 시트 대신 각 기준별로 나눠서 저장 (엑셀 표로)
    for method in ['CVaR', 'Sortino', 'Variance', 'Sharpe']:
        df_method = df_weights[df_weights['최적화 기준'] == method]
        df_method.to_excel(writer, index=False, sheet_name=f'포트비중_{method}')
        ws = writer.sheets[f'포트비중_{method}']
        (mr, mc) = df_method.shape
        ws.add_table(0, 0, mr, mc - 1, {
            'columns': [{'header': col} for col in df_method.columns],
            'style': 'Table Style Medium 9'
        })

    # 포트폴리오통계 시트도 엑셀 표로
    df_stats.to_excel(writer, index=False, sheet_name='포트폴리오통계')
    ws_stats = writer.sheets['포트폴리오통계']
    (mr_stats, mc_stats) = df_stats.shape
    ws_stats.add_table(0, 0, mr_stats, mc_stats - 1, {
        'columns': [{'header': col} for col in df_stats.columns],
        'style': 'Table Style Medium 9'
    })

    # 뉴스 데이터프레임 시트 생성 및 표 적용
    news_df.to_excel(writer, index=False, sheet_name='종목뉴스')
    ws_news = writer.sheets['종목뉴스']
    (nr, nc) = news_df.shape
    ws_news.add_table(0, 0, nr, nc - 1, {
        'columns': [{'header': col} for col in news_df.columns],
        'style': 'Table Style Medium 9'
    })
    autofit_columns_and_wrap(ws_news, news_df, writer.book)

    workbook  = writer.book
    worksheet = writer.sheets['종목분석']

    # Define column widths you want (by column name)
    col_widths = {
        '티커':6,
        '종목': 25,
        'B-Score':6,
        '업종': 25,
        '주가(1개월대비)': 15,
        '부채비율':6,
        '유동비율':6,
        'PBR':6,
        'PER(업종)': 7,
        'ICR':6,
        "FCF성장률": 10,
        'EPS성장률': 10,
        '배당성장률': 10,
        '영업이익률(Y/Q)': 10,
        '모멘텀':6,
        '거래량':6,
        '합계점수':6,
    }

    # Set widths for specified columns
    for col_name, width in col_widths.items():
        if col_name in df.columns:
            col_idx = df.columns.get_loc(col_name)
            worksheet.set_column(col_idx, col_idx, width)

    
    bscore_col_idx = df.columns.get_loc('B-Score')
    
    start_row = 0  # data starts after header row 1
    end_row = len(df)
    start_col = 0
    end_col = len(df.columns) - 1
    
    def xl_col(col_idx):
        div = col_idx + 1
        string = ""
        while div > 0:
            div, mod = div // 26, div % 26
            if mod == 0:
                mod = 26
                div -= 1
            string = chr(64 + mod) + string
        return string
    
    first_cell = f"{xl_col(start_col)}{start_row + 1}"
    last_cell = f"{xl_col(end_col)}{end_row + 1}"
    data_range = f"{first_cell}:{last_cell}"
    
    bscore_col_letter = xl_col(bscore_col_idx)
    
    # 1) Add Excel table for the data
    worksheet.add_table(data_range, {
        'columns': [{'header': col} for col in df.columns],
        'style': 'Table Style Medium 9' 
    })
    
    # 2) Gradient on B-Score column (dynamic min/max)
    bscore_range = f"{bscore_col_letter}{start_row + 1}:{bscore_col_letter}{end_row + 1}"
    
    worksheet.conditional_format(bscore_range, {
        'type': '3_color_scale',
        'min_type': 'min',
        'mid_type': 'percentile',
        'mid_value': 50,
        'max_type': 'max',
        'min_color': "#FF0000",
        'mid_color': "#FFFF00",
        'max_color': "#00FF00"
    })
    #############
    # Get the column index for '합계점수'
    total_score_col_idx = df.columns.get_loc('합계점수')

    # Column letter for '합계점수'
    total_score_col_letter = xl_col(total_score_col_idx)

    # 2) Add gradient formatting on '합계점수' column
    total_score_range = f"{total_score_col_letter}{start_row + 1}:{total_score_col_letter}{end_row + 1}"

    worksheet.conditional_format(total_score_range, {
        'type': '3_color_scale',
        'min_type': 'min',
        'mid_type': 'percentile',
        'mid_value': 50,
        'max_type': 'max',
        'min_color': "#FF0000",
        'mid_color': "#FFFF00",
        'max_color': "#00FF00"
    })

    #############
    pbr_col_idx = df.columns.get_loc('PBR')
    pbr_col_letter = xl_col(pbr_col_idx)
    pbr_range = f"{pbr_col_letter}{start_row + 2}:{pbr_col_letter}{end_row + 1}"

    yellow_format = workbook.add_format({'bg_color': '#FFFF00', 'font_color': '#000000'})
    orange_format = workbook.add_format({'bg_color': '#FFA500', 'font_color': '#000000'})  # 오렌지색


    # 주황색 조건 (PBR > 10)
    worksheet.conditional_format(pbr_range, {
        'type': 'cell',
        'criteria': '>',
        'value': 10,
        'format': orange_format
    })

    # Create formats
    right_align_format = workbook.add_format({'align': 'right'})
    center_align_format = workbook.add_format({'align': 'center'})

    # Write header (row 0) without formatting
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value)

    # Write data rows with formatting based on column
    for row_num, row_data in enumerate(df.values, start=1):
        for col_num, cell_value in enumerate(row_data):
            col_name = df.columns[col_num]
            
            if col_name in ['PER(업종)', 'ROE(업종)', 'ROA(업종)', '부채비율', '유동비율', 'ICR', '거래량']:
                fmt = right_align_format
            elif col_name in ['EPS성장률', '배당성장률', '영업이익률(Y/Q)', '영업이익률(Y)', 'FCF성장률', 'FCF수익률']:
                fmt = center_align_format
            else:
                fmt = None

            worksheet.write(row_num, col_num, cell_value, fmt)


##########################################################################################################
time.sleep(3)

excel_path = f'result_US_{formattedDate}.xlsx'


date_kr = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%-m월 %-d일')
date_kr_month = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%-m월')
date_kr_ymd = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%Y년 %-m월 %-d일')  # Unix

#########################################################################################################
def generate_prompt(df_stocks: pd.DataFrame, df_news: pd.DataFrame) -> str:
    top_limit = 50
    ai_pick = 10
    top_stocks = df_stocks.sort_values(by='합계점수', ascending=False).head(top_limit)
    tickers = top_stocks['티커'].tolist()

    news_summary = []
    if {'기업명', '감정지수', '뉴스 요약'}.issubset(df_news.columns):
        grouped = df_news.groupby('기업명')
        for comp, group in grouped:
            avg_sent = group['감정지수'].mean()
            recent_summaries = group.sort_values(by='발행일', ascending=False)['뉴스 요약'].head(3).tolist()
            summaries_text = ' / '.join([s for s in recent_summaries if s])
            news_summary.append(f"{comp}: 평균 감정지수 {avg_sent:.2f}, 최근 뉴스 요약: {summaries_text}")

    prompt = f"""
당신은 기업 분석 및 거시경제 분석에 능숙한 전문 주식 분석가입니다. 반드시 한국어로 답변해 주세요. {date_kr_ymd}기준 주식 데이터와 뉴스 감정 지수 및 뉴스 요약 정보를 활용하여 다음 작업을 수행해 주세요.

주요 종목 목록 (장기 재무건정성 + 중장기 모멘텀 합계점수 순 상위 {top_limit}개 티커): {', '.join(tickers)}.

뉴스 요약 및 감정 지수:
{chr(10).join(news_summary)}


위 데이터를 바탕으로, {date_kr_ymd}기준 각 종목의 장기적인 경쟁 우위 정보와 투자 매력을 찾아주세요.
그리고 이 중 다음 한 달간 가장 상승 가능성이 높은 {ai_pick}개 종목을 선정하고, 
각 종목별로 명확하고 타당한 근거를 함께 설명해 주세요.

결과는 {ai_pick}개 종목과 그 이유를 간결하게 불릿 포인트로 알려 주세요.

추가로, {date_kr_ymd}기준 거시경제 상황(예: 관세, 금리, 인플레이션 등 주요 이슈)과 미국 증시에 미치는 영향에 대한 간략한 요약도 포함해 주세요.

"""

    return prompt.strip()

##########################################################################################################
# Initialize the client (picks up your API key automatically from env vars, or pass api_key explicitly)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

##########################################################################################################
def query_gemini(prompt: str) -> str:
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    temperature=0.2,
)
    return response.text


def main(df_stocks, df_news):
    prompt = generate_prompt(df_stocks, df_news)
    print("Prompt sent to Gemini:\n", prompt)

    answer = query_gemini(prompt)
    return answer

answer = main(df, news_df)

#########################################################################################################

msg = EmailMessage()
msg['Subject'] = f'[{date_kr}] 美증시 퀀트 분석 리포트'
msg['From'] = Address(display_name='Hyungsuk Choi', addr_spec=EMAIL)
msg['To'] = ''  # or '' or a single address to satisfy the 'To' header requirement

content = (
    f"귀하의 중장기 투자 참고를 위해 {date_kr} 기준, "
    f"시가총액 상위 {limit}개 상장기업에 대한 최신 퀀트 분석 자료를 전달드립니다. "
    "각 기업의 재무 점수는 ‘B-Score’, 중장기 모멘텀을 포함한 총점수는 '종합점수' 항목을 참고해 주시기 바랍니다.\n\n"
    "본 자료는 워런 버핏의 투자 철학을 기반으로, "
    "기업의 재무 건전성을 수치화하여 평가한 결과입니다. "
    "투자 판단 시에는 정성적 요소에 대한 별도의 면밀한 검토도 "
    "함께 병행하시기를 권장드립니다.\n\n"
    "📌주요 재무지표 해설\n"
    "D/E 부채비율 (Debt to Equity): 자본 대비 부채의 비율로, 재무 건전성을 나타냅니다. 낮을수록 안정적입니다.\n"
    "CR 유동비율 (Current Ratio): 유동자산이 유동부채를 얼마나 커버할 수 있는지를 보여줍니다.\n"
    "PBR 주가순자산비율 (Price to Book Ratio): 주가가 장부가치 대비 얼마나 높은지를 나타내며, 1보다 낮으면 저평가로 해석되기도 합니다.\n"
    "PER 주가수익비율 (Price to Earnings Ratio): 이익 대비 주가 수준을 나타냅니다. 낮을수록 이익 대비 저렴한 기업입니다.\n"
    "ROE 자기자본이익률 (Return on Equity): 자본을(부채 미포함) 얼마나 효율적으로 운용해 이익을 냈는지를 나타냅니다.\n"
    "ROA 총자산이익률 (Return on Assets): 총자산(부채 포함) 대비 수익률로, 보수적인 수익성 지표입니다.\n"
    "ICR 이자보상비율 (Interest Coverage Ratio): 영업이익으로 이자비용을 얼마나 감당할 수 있는지 나타냅니다.\n"
    "EPS 주당순이익 (Earnings Per Share): 최근 5년간 1주당 기업이 창출한 순이익의 성장률로, 수익성과 성장성 판단에 유용합니다.\n"
    "배당성장률: 최근 10년간 배당금의 성장률을 나타내는 지표입니다.\n"
    "영업이익률: 최근 5개 영업년도/분기의 평균 영업이익률 성장률로, 기업의 수익성 수준을 보여줍니다.\n"
    "모멘텀: 주가의 중장기 상승 흐름을 반영한 지표로, 주가의 탄력과 추세를 평가합니다.\n\n"
    "ESG: 기업의 지속가능성을 나타내는 지표로, 동종업계 대비 수준과 함께 평가합니다. (LAG: 뒤쳐짐, AVG: 평균, LEAD: 우수)\n\n"
    "해당 메일은 매주 평일 오후 5시에 자동 발송되며, 안정적이고 현명한 투자를 위한 참고 자료로 제공됩니다.\n\n"
    "귀하의 성공적인 투자를 응원합니다."
)

msg.set_content(content)
html_content = f"""
<html>
  <body>
    <p>귀하의 중장기 투자 참고를 위해 <b>{date_kr}</b> 기준, 
    시가총액 상위 <b>{limit}</b>개, 뉴욕증권거래소(NYSE), 나스닥(NASDAQ), 아멕스(AMEX)에 상장된 기업들의 최신 퀀트 데이터를 전달드립니다.</p>

    <p>각 기업의 재무 점수는 <b>B-Score</b>, 중장기 모멘텀을 포함한 총점수는 <b>종합점수</b> 항목을 참고해 주시기 바랍니다.</p>

    <h3>📌 주요 재무지표 해설</h3>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; font-family: sans-serif;">
      <thead style="background-color: #f2f2f2;">
        <tr>
          <th>지표</th>
          <th>한글명</th>
          <th>설명</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><b>FCF</b></td><td>자유현금흐름</td><td>기업이 영업활동을 통해 벌어들인 현금에서 설비 투자 등 사업 유지를 위해 지출한 자금을 제외한 후, 실제로 기업이 자유롭게 사용할 수 있는 현금입니다. 이 현금은 신규 투자 등 다양한 용도로 활용될 수 있습니다.</td></tr>
        <tr><td><b>추정DCF범위</b></td><td>할인된 현금흐름</td><td>미래 예상 자유현금흐름(FCF)을 보수적인 할인율로 현재 가치로 환산하여 산출한 기업의 내재가치입니다. 본 내재가치는 몬테카를로 시뮬레이션을 통해 여러 성장 시나리오를 고려하며, 95% 신뢰구간 범위 내에서 내재가치 변동성을 평가하여 기업의 저평가 여부를 보다 정밀하게 판단합니다.</td></tr>
        <tr><td><b>D/E</b></td><td>부채비율</td><td>자본 대비 부채의 비율로, 재무 건전성을 나타냅니다. 낮을수록 안정적입니다.</td></tr>
        <tr><td><b>CR</b></td><td>유동비율</td><td>유동자산이 유동부채를 얼마나 커버할 수 있는지를 보여줍니다.</td></tr>
        <tr><td><b>PBR</b></td><td>주가순자산비율</td><td>주가가 장부가치 대비 얼마나 높은지를 나타내며, 1보다 낮으면 저평가로 해석되기도 합니다.</td></tr>
        <tr><td><b>PER</b></td><td>주가수익비율</td><td>이익 대비 주가 수준을 나타냅니다. 낮을수록 이익 대비 저렴한 기업입니다.</td></tr>
        <tr><td><b>ROE</b></td><td>자기자본이익률</td><td>자본을(부채 미포함) 얼마나 효율적으로 운용해 이익을 냈는지를 나타냅니다.</td></tr>
        <tr><td><b>ROA</b></td><td>총자산이익률</td><td>총자산(부채 포함) 대비 수익률로, 보수적인 수익성 지표입니다.</td></tr>
        <tr><td><b>ICR</b></td><td>이자보상비율</td><td>영업이익으로 이자비용을 얼마나 감당할 수 있는지 나타냅니다.</td></tr>
        <tr><td><b>FCF수익률</b></td><td>-</td><td>자유현금흐름(FCF)을 시가총액으로 나눈 비율로, 이 비율이 높을수록 기업이 창출하는 현금 대비 주가가 저평가되었음을 의미합니다.</td></tr>
        <tr><td><b>FCF성장률</b></td><td>-</td><td>최근 5년간 자유현금흐름의 성장률을 나타내는 지표입니다.</td></tr>
        <tr><td><b>EPS</b></td><td>주당순이익</td><td>최근 5년간 1주당 기업이 창출한 순이익의 성장률로, 수익성과 성장성 판단에 유용합니다.</td></tr>
        <tr><td><b>배당성장률</b></td><td>-</td><td>최근 10년간 배당금의 성장률을 나타내는 지표입니다.</td></tr>
        <tr><td><b>영업이익률</b></td><td>-</td><td>최근 4개 영업년도/분기의 평균 영업이익률 성장률로, 기업의 수익성 수준을 보여줍니다.</td></tr>
        <tr><td><b>모멘텀</b></td><td>-</td><td>주가의 중장기 상승 흐름을 반영한 지표로, 주가의 탄력과 추세를 평가합니다.</td></tr>
        <tr><td><b>ESG</b></td><td>-</td><td>기업의 지속가능성을 나타내는 지표로, 동종업계 대비 수준과 함께 평가합니다.</td></tr>
        <tr><td><b>CVaR</b></td><td>조건부 위험가치</td><td>포트폴리오가 극단적인 손실을 겪을 경우, 손실이 발생하는 최악 5% 구간 내에서 평균적으로 얼마나 손실이 발생하는지를 나타내는 지표입니다.</td></tr>
        <tr><td><b>Sortino Ratio</b></td><td>소티노 지수</td><td>수익률 대비 하방 위험(손실 변동성)을 고려한 위험 조정 수익률을 나타냅니다. 값이 높을수록 하방 위험 대비 수익률이 우수함을 의미합니다.</td></tr>
        <tr><td><b>Variance</b></td><td>분산</td><td>포트폴리오 수익률의 변동성을 나타내는 지표로, 위험 수준 평가에 사용됩니다. 값이 낮을수록 안정적인 포트폴리오임을 뜻합니다.</td></tr>
        <tr><td><b>Sharpe Ratio</b></td><td>샤프 지수</td><td>포트폴리오의 초과 수익률을 표준편차로 나눈 지표로, 위험 대비 수익률을 평가합니다. 값이 클수록 효율적인 투자임을 나타냅니다.</td></tr>
        <tr><td><b>Sentiment Score</b></td><td>감성 점수</td><td>텍스트의 긍정 또는 부정 정도를 수치화한 지표로, 투자 심리나 뉴스 반응을 정량적으로 평가합니다. 값이 높을수록 긍정적인 정서임을 나타냅니다.</td></tr>
      </tbody>
    </table>

    <h3 style="margin-top: 30px;"><strong>📊 {date_kr_month} AI 추천 종목 및 거시경제 분석</strong></h3>

    <p>{answer}</p>

    <p style="margin-top: 20px; font-size: 14px; color: #444;">
    본 자료는 <strong>워런 버핏의 '가치투자'</strong> (기업의 내재가치보다 시장 가격이 낮을 때 매수해, 가격이 가치에 수렴할 때 차익을 얻는 투자 방식) 철학을 기반으로,<br>
    기업의 재무 건전성을 수치화하여 평가한 결과입니다.<br>
    투자 판단 시에는 정성적 요소에 대한 별도의 면밀한 검토도 함께 병행하시기를 권장드립니다.
    </p>

    <p><em>해당 메일은 매주 월, 수, 금, 일요일 오전 8시에 자동 발송되며, 안정적이고 현명한 투자를 위한 참고 자료로 제공됩니다.</em></p>

    <p><b>귀하의 성공적인 투자를 응원합니다.</b></p>
  </body>
</html>
"""

msg.add_alternative(html_content, subtype='html')

with open(excel_path, 'rb') as f:
    msg.add_attachment(f.read(), maintype='application',
                       subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                       filename=excel_path)

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL, PASSWORD)
    smtp.send_message(msg, to_addrs=recipients)  # send_message's to_addrs param controls actual recipients

