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
from scipy.stats import linregress
from datetime import datetime, timedelta
from google import genai
from google.genai import types
import json
import markdown


################ DEPENDENCIES ###########################

# pip install -r requirements.txt

#########################################################


################ PREDETERMINED FIELDS ###################


fmp_key = ''
NUM_THREADS = 2 #multithreading 

country = 'US'
limit=20 # max 250 requests/day
sp500 = True

# top X tickers to optimize
opt = 10 

#for news
news_lookup = 100

#for moat
moat_limit = 50
#########################################################



# print('May take up to few minutes...')
 
today = dt.datetime.today().weekday()
weekend = today - 4 # returns 1 for saturday, 2 for sunday
formattedDate = (dt.datetime.today() - dt.timedelta(days = weekend)).strftime("%Y%m%d") if today >= 5 else dt.datetime.today().strftime("%Y%m%d")

three_months_approx = dt.datetime.today() - dt.timedelta(days=90)
formattedDate_3m_ago =  three_months_approx.strftime("%Y%m%d")

date_kr = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%-m월 %-d일')
date_kr_month = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%-m월')
date_kr_ymd = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%Y년 %-m월 %-d일')  # Unix

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
    
import pandas as pd
import numpy as np

def safe_check(val):
    return val is not None and not (isinstance(val, float) and np.isnan(val))

def quant_style_score(
    price_vs_fair_upper=None,
    price_vs_fair_lower=None,
    fcf_yield_rank=None,
    fcf_vs_treasury_spread=None,
    per=None,
    per_rank=None,
    pbr_rank=None,
    de=None,
    cr=None,
    industry_per=None,
    roe_z=None,
    roa_z=None,
    roe=None,
    roa=None,
    icr=None,
    fcf_cagr_rank=None,
    eps_cagr_rank=None,
    div_cagr_rank=None,
    eps=None,
    div_yield=None,
    opinc_yoy=None,
    opinc_qoq=None,
    industry_roe=None,
    industry_roa=None
):
    valuation_score = 0
    earnings_momentum_score = 0

    # Valuation
    if safe_check(price_vs_fair_upper) and price_vs_fair_upper > 0:
        valuation_score += min(price_vs_fair_upper * 3, 3)
    if safe_check(price_vs_fair_lower) and price_vs_fair_lower > 0:
        valuation_score += min(price_vs_fair_lower * 4, 3)
    if safe_check(fcf_vs_treasury_spread):
        if fcf_vs_treasury_spread > 0:
            valuation_score += min(fcf_vs_treasury_spread * 10, 2)
        else:
            valuation_score -= 1
    if safe_check(fcf_yield_rank):
        valuation_score += fcf_yield_rank * 2
    if safe_check(per_rank):
        valuation_score += (1 - per_rank) * 2
    if safe_check(per) and safe_check(industry_per):
        if per < industry_per * 0.7:
            valuation_score += 0.5
        elif per > industry_per * 1.3:
            valuation_score -= 0.5
    if safe_check(pbr_rank):
        valuation_score += (1 - pbr_rank) * 1.5
    if safe_check(de):
        if 0 < de <= 0.5:
            valuation_score += 1
        elif de > 1.0:
            valuation_score -= 1
    if safe_check(cr):
        if 1.5 <= cr <= 2.5:
            valuation_score += 1
        elif cr < 1.0:
            valuation_score -= 0.5

    # Earnings / Momentum
    if safe_check(roe_z):
        earnings_momentum_score += min(max(roe_z, -2), 2)
    if safe_check(roa_z):
        earnings_momentum_score += min(max(roa_z, -2), 2)
    if not safe_check(roe_z) and safe_check(industry_roe) and safe_check(roe):
        if roe > industry_roe:
            earnings_momentum_score += 0.5
    if not safe_check(roa_z) and safe_check(industry_roa) and safe_check(roa):
        if roa > industry_roa:
            earnings_momentum_score += 0.5
    if safe_check(icr):
        if icr >= 10:
            earnings_momentum_score += 1
        elif icr >= 5:
            earnings_momentum_score += 0.5
        elif icr < 1:
            earnings_momentum_score -= 0.5
    if safe_check(fcf_cagr_rank):
        earnings_momentum_score += fcf_cagr_rank * 2
    if safe_check(eps_cagr_rank):
        earnings_momentum_score += eps_cagr_rank * 2
    if safe_check(div_cagr_rank):
        earnings_momentum_score += div_cagr_rank * 1.5
    if safe_check(eps):
        if eps >= 0.3:
            earnings_momentum_score += 2
        elif eps >= 0.1:
            earnings_momentum_score += 1
        elif eps < 0:
            earnings_momentum_score -= 1
    if safe_check(div_yield):
        if div_yield >= 0.1:
            earnings_momentum_score += 1.0
        elif div_yield >= 0.08:
            earnings_momentum_score += 0.75
        elif div_yield >= 0.06:
            earnings_momentum_score += 0.5
        elif div_yield < 0.02:
            earnings_momentum_score -= 0.5
    if safe_check(opinc_yoy):
    # YoY 성장률 크기에 따라 가중치 부여 (예: 0~2 범위)
        if opinc_yoy > 0.2:
            earnings_momentum_score += 2
        elif opinc_yoy > 0.05:
            earnings_momentum_score += 1
        else:
            earnings_momentum_score += 0

        # 마이너스면 페널티
        if opinc_yoy < 0:
            earnings_momentum_score -= 1

    if safe_check(opinc_qoq):
        # QoQ 성장률도 강도에 따라 가중치 차등 부여
        if opinc_qoq > 0.1:
            earnings_momentum_score += 1
        elif opinc_qoq > 0:
            earnings_momentum_score += 0.5
        elif opinc_qoq < 0:
            earnings_momentum_score -= 0.5
    return round(valuation_score, 2), round(earnings_momentum_score, 2)



def get_fcf_yield_and_cagr(ticker, yf_ticker, api_key="YOUR_API_KEY"):
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
            
            market_cap = ticker.info.get('marketCap')
            if market_cap is None or market_cap == 0:
                return (None, None, [])

            cashflow_df = ticker.cashflow
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


    result = try_yf(yf_ticker)
    if result is not None and (
        result[0] is not None or result[1] is not None or (result[2] and len(result[2]) > 0)
    ):
        return result


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
        stock = ticker
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




def compute_eps_growth_slope(ticker):
    try:
        income_stmt = ticker.financials  # Annual financials DataFrame
        
        if "Diluted EPS" not in income_stmt.index:
            return None

        eps_series = income_stmt.loc["Diluted EPS"].dropna()
        eps_series = eps_series.sort_index()  # Oldest to newest

        # Keep last 5 years
        current_year = dt.datetime.today().year
        eps_series = eps_series[[col for col in eps_series.index if col.year >= current_year - 5]]

        if len(eps_series) < 2:
            return None

        eps_list = eps_series.tolist()

        x = list(range(len(eps_list)))
        slope, _, _, _, _ = linregress(x, eps_list)
        return slope

    except Exception:
        return None

    
# gets the most recent interest coverage ratio available
def get_interest_coverage_ratio(ticker):
    financials = ticker.financials # Annual financials, columns = dates (most recent first)
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
        esg = ticker.sustainability
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

def get_industry_per(ind):
    try: 
        if ind is not None:
            ans = float(df_per.filter(pl.col('Industry') == ind).select("P/E Ratio").item())
            return ans
        return per
    except Exception:
        spy = yf.Ticker('SPY')
        spy_info = spy.info
        per = spy_info.get('trailingPE')
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

prohibited = {'AFA', 'ACH', 'BACRP', 'CDVM', 'NVL', 'TBB', 'TBC', 'VZA', "ANTM","SOJD","SOJE","SOJC","RY-PT","DUKB"} # no data on yfinance or frequently cause errors
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

def score_momentum(ma, ma_lt, ret_20d, ret_60d, rsi, macd):
    score = 0

    # 이동평균 크로스오버 (단기, 장기)
    if ma:           # 단기 MA 크로스 오버 신호 (True/False)
        score += 10
    if ma_lt:        # 장기 MA 크로스 오버 신호 (True/False)
        score += 15

    # 단기 수익률 반영 (예: 20일 수익률)
    if ret_20d is not None:
        if ret_20d > 0:
            score += min(ret_20d * 100, 10)  # 0~10점, 1% 상승시 1점

    # 중기 수익률 반영 (예: 60일 수익률)
    if ret_60d is not None:
        if ret_60d > 0:
            score += min(ret_60d * 100, 15)  # 0~15점

    # RSI 과매도 반등 (True/False)
    if rsi:
        score += 20

    # MACD 골든크로스 (True/False)
    if macd:
        score += 20

    return round(score, 2)

def get_operating_income_yoy(ticker_obj):
    try:
        financials = ticker_obj.financials

        if "Operating Income" not in financials.index:
            return None

        operating_income = financials.loc["Operating Income"].dropna()
        operating_income = operating_income.sort_index()  # 오래된 순 정렬

        if len(operating_income) < 2:
            return None

        # 최근 2년치 영업이익
        latest = operating_income.iloc[-1]
        prev = operating_income.iloc[-2]

        if prev == 0:
            return None  # 0으로 나누기 방지

        yoy_growth = (latest - prev) / abs(prev)
        return yoy_growth

    except Exception:
        return None

def get_operating_income_qoq(ticker_obj):
    try:
        financials = ticker_obj.quarterly_financials

        if "Operating Income" not in financials.index:
            return None

        operating_income = financials.loc["Operating Income"].dropna()
        operating_income = operating_income.sort_index()  # 오래된 순 정렬

        if len(operating_income) < 2:
            return None

        latest = operating_income.iloc[-1]
        prev = operating_income.iloc[-2]

        if prev == 0:
            return None

        qoq_growth = (latest - prev) / abs(prev)
        return qoq_growth

    except Exception:
        return None


    
def score_intrinsic_value(conf_lower, conf_upper, current_price, fcf_yield, tenyr_treasury_yield, fcf_cagr):
    score = 0

    if conf_lower is not None and conf_upper is not None and current_price is not None:
        if current_price < conf_upper:
            score += 2  # price is within fair value range
            if current_price <= conf_lower:
                score += 3  # price is at or below lower bound of fair value range
        else:
            score -= 3  # price outside fair value range

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
    info,
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
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info
            beta = info.get("beta", None)
            name = info.get("shortName", ticker)
            industry = info.get("industry", None)
            currentPrice = info.get("currentPrice", None)
            percentage_change = get_percentage_change(ticker)

            # Valuation & Liquidity
            debtToEquity = info.get('debtToEquity', None)
            debtToEquity = debtToEquity / 100 if debtToEquity is not None else None
            currentRatio = info.get('currentRatio', None)
            pbr = info.get('priceToBook', None)
            per = info.get('trailingPE', None)

            # Industry
            industry_per = get_industry_per(industry)
            industry_per = round(industry_per) if industry_per is not None else None
            industry_roe = get_industry_roe(industry)
            industry_roa = get_industry_roa(industry)

            # Profitability
            roe = info.get('returnOnEquity', None)
            roa = info.get('returnOnAssets', None)
            icr = get_interest_coverage_ratio(yf_ticker)

            # Growth
            eps_cagr = compute_eps_growth_slope(yf_ticker)
            div_cagr = has_stable_dividend_growth_cagr(yf_ticker)
            opinc_yoy = get_operating_income_yoy(yf_ticker)
            opinc_qoq = get_operating_income_qoq(yf_ticker)

            # FCF & Valuation
            fcf_yield, fcf_cagr, fcf_list = get_fcf_yield_and_cagr(ticker, yf_ticker, api_key=fmp_key)
            tenyr_treasury_yield = get_10yr_treasury_yield()
            discount_rate = (tenyr_treasury_yield + (beta * 5.0)) / 100.0 if beta is not None else (tenyr_treasury_yield + 5.0) / 100.0
            terminal_growth_rate = 0.02

            initial_fcf = fcf_list[-1] if fcf_list and fcf_list[-1] is not None else None

            intrinsic_value_range = (
                monte_carlo_dcf_valuation(
                    info, initial_fcf, discount_rate, terminal_growth_rate,
                    projection_years=5, num_simulations=10_000
                ) if initial_fcf is not None else (None, None)
            )

            result = {
                "ticker": ticker,
                "name": name,
                "price": currentPrice,
                "price_vs_fair_upper": ((intrinsic_value_range[1] - currentPrice) / currentPrice) if intrinsic_value_range[1] and currentPrice else None,
                "price_vs_fair_lower": ((intrinsic_value_range[0] - currentPrice) / currentPrice) if intrinsic_value_range[0] and currentPrice else None,
                "fcf_yield": fcf_yield,
                "per": per,
                "pbr": pbr,
                "de": debtToEquity,
                "cr": currentRatio,
                "roe": roe,
                "roa": roa,
                "icr": icr,
                "fcf_cagr": fcf_cagr,
                "eps_cagr": eps_cagr if isinstance(eps_cagr, float) else None,
                "div_cagr": div_cagr if isinstance(div_cagr, float) else None,
                "eps": eps_cagr if isinstance(eps_cagr, float) else None,
                "div_yield": info.get('dividendYield', div_cagr) if div_cagr is not None else None,
                "opinc_yoy": opinc_yoy if isinstance(opinc_yoy, float) else None,
                "opinc_qoq": opinc_qoq if isinstance(opinc_qoq, float) else None,

                # Industry benchmarks
                "industry_per": industry_per,
                "industry_roe": industry_roe,
                "industry_roa": industry_roa,

                # NEW: fields needed for quant_style_score (will be filled later)
                "fcf_yield_rank": None,
                "per_rank": None,
                "pbr_rank": None,
                "fcf_cagr_rank": None,
                "eps_cagr_rank": None,
                "div_cagr_rank": None,
                "roe_z": None,
                "roa_z": None,

                # Misc.
                "industry":industry,
                "1M_Change": percentage_change,
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
#############################################################################
# Rank 계산
df["fcf_yield_rank"] = df["fcf_yield"].rank(pct=True)
df["per_rank"] = 1 - df["per"].rank(pct=True)
df["pbr_rank"] = 1 - df["pbr"].rank(pct=True)
df["fcf_cagr_rank"] = df["fcf_cagr"].rank(pct=True)
df["eps_cagr_rank"] = df["eps_cagr"].rank(pct=True)
df["div_cagr_rank"] = df["div_cagr"].rank(pct=True)
# 업종별 통계 계산
industry_stats = df.groupby("industry").agg({
    "roe": ["mean", "std"],
    "roa": ["mean", "std"]
})

industry_stats.columns = ['_'.join(col).strip() for col in industry_stats.columns.values]
industry_stats.index.name = "industry"

df = df.merge(industry_stats, left_on="industry", right_index=True, how="left")

def safe_z(x, mean, std):
    if pd.isna(x) or pd.isna(mean) or pd.isna(std) or std == 0:
        return 0
    return (x - mean) / std

df["roe_z"] = df.apply(lambda row: safe_z(row["roe"], row["roe_mean"], row["roe_std"]), axis=1)
df["roa_z"] = df.apply(lambda row: safe_z(row["roa"], row["roa_mean"], row["roa_std"]), axis=1)


def compute_quant_scores(df, tenyr_yield):
    scores = []
    for _, row in df.iterrows():
        valuation_score, momentum_score = quant_style_score(
            price_vs_fair_upper=row["price_vs_fair_upper"],
            price_vs_fair_lower=row["price_vs_fair_lower"],
            fcf_yield_rank=row["fcf_yield_rank"],
            fcf_vs_treasury_spread=row["fcf_yield"] - tenyr_yield if row["fcf_yield"] is not None else None,
            per=row["per"],
            per_rank=row["per_rank"],
            pbr_rank=row["pbr_rank"],
            de=row["de"],
            cr=row["cr"],
            industry_per=row["industry_per"],
            roe_z=row["roe_z"],
            roa_z=row["roa_z"],
            roe=row["roe"],        # 추가
            roa=row["roa"],        # 추가
            icr=row["icr"],
            fcf_cagr_rank=row["fcf_cagr_rank"],
            eps_cagr_rank=row["eps_cagr_rank"],
            div_cagr_rank=row["div_cagr_rank"],
            eps=row["eps"],
            div_yield=row["div_yield"],
            opinc_yoy=row["opinc_yoy"],
            opinc_qoq=row["opinc_qoq"],
            industry_roe=row["industry_roe"],
            industry_roa=row["industry_roa"]
        )
        scores.append({
            "ticker": row["ticker"],
            "valuation_score": valuation_score,
            "momentum_score": momentum_score,
            "total_score": valuation_score + momentum_score
        })
    return pd.DataFrame(scores)


###############
def compute_price_flow_scores(df_main, df_batch_result):
    scores = []
    for ticker in df_main['ticker']:
        row = df_batch_result.loc[df_batch_result['Ticker'] == ticker]
        if row.empty:
            scores.append(None)
            continue
        
        ma = bool(row['ma_crossover'].values[0])
        ma_lt = bool(row['ma_crossover_lt'].values[0])
        ret20 = row['return_20d'].values[0]
        ret60 = row['return_60d'].values[0]
        rsi = bool(row['rsi_rebound'].values[0])
        macd = bool(row['macd_golden_cross'].values[0])
        
        score = score_momentum(ma, ma_lt, ret20, ret60, rsi, macd)
        scores.append(score)
    return scores

# 메인 df에 price_flow_score 컬럼 추가
# Step 1: price_flow_score 먼저 계산
df['price_flow_score'] = compute_price_flow_scores(df, df_batch_result)

# Step 2: 퀀트 점수 계산 (valuation_score, momentum_score, total_score 등)
tenyr_yield = get_10yr_treasury_yield()
score_df = compute_quant_scores(df, tenyr_yield)

# Step 3: 두 결과 merge (이때 total_score가 생김)
final_df = df.merge(score_df, on="ticker", how="left")

# Step 4: total_score에 price_flow_score 더하기
final_df['total_score'] = final_df['total_score'].fillna(0) + final_df['price_flow_score'].fillna(0)

def normalize_series(series):
    min_val = series.min()
    max_val = series.max()
    if pd.isna(min_val) or pd.isna(max_val) or min_val == max_val:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val) * 100  # ✅ Scale to 0–100

# Normalize each category to 0–100
final_df['valuation_score_norm'] = normalize_series(final_df['valuation_score'])
final_df['momentum_score_norm'] = normalize_series(final_df['momentum_score'])
final_df['price_flow_score_norm'] = normalize_series(final_df['price_flow_score'].fillna(0))

# Add up and average
final_df['total_score'] = (
    final_df['valuation_score_norm'] +
    final_df['momentum_score_norm'] +
    final_df['price_flow_score_norm']
) / 3  # ✅ Final score out of 100


# Round the normalized scores and total
score_cols = [
    "valuation_score_norm",
    "momentum_score_norm",
    "price_flow_score_norm",
    "total_score"
]

final_df[score_cols] = final_df[score_cols].round()


# 컬럼 선택
export_columns_kr = [
    "종목", "업종", "현재가", "1개월대비",
    "밸류에이션", "실적모멘텀", "가격/수급",
    "총점수"
]


rename_dict = {
    "ticker": "종목",
    "industry": "업종",
    "price": "현재가",
    "1M_Change": "1개월대비",
    "valuation_score_norm": "밸류에이션",
    "momentum_score_norm": "실적모멘텀",
    "price_flow_score_norm": "가격/수급",
    "total_score": "총점수"
}
final_df = final_df.rename(columns=rename_dict)

# total_score 기준 정렬
final_df = final_df.sort_values(by='총점수', ascending=False).reset_index(drop=True)

# 한글 컬럼명 매핑 딕셔너리

# 컬럼명 변경


# 이후에 export_columns도 한글명으로 변경해야 엑셀 내 컬럼명이 한글로 나옵니다
export_columns_kr = list(rename_dict.values())

# 정렬 및 엑셀 저장시 export_columns_kr 사용

# 예시: 엑셀 저장
final_df[export_columns_kr].to_excel("quant_results_kr.xlsx", index=False)

# 엑셀 저장
with pd.ExcelWriter("quant_results.xlsx", engine="xlsxwriter") as writer:
    final_df[export_columns_kr].to_excel(writer, index=False, sheet_name="Quant Results")

    workbook = writer.book
    worksheet = writer.sheets["Quant Results"]

    # 줄바꿈 포맷 설정
    wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})

    # 컬럼 너비 자동 조정
    for i, col in enumerate(export_columns_kr):
        col_data = final_df[col].astype(str)
        max_len = max(col_data.map(len).max(), len(str(col)))
        width = min(max_len + 2, 50)
        worksheet.set_column(i, i, width, wrap_format)

