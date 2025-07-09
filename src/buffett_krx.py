
# SPDX-FileCopyrightText: © 2025 Hyungsuk Choi <chs_3411@naver[dot]com>, University of Maryland 
# SPDX-License-Identifier: MIT

import yfinance as yf
import pandas as pd
from pykrx import stock
#from dotenv import load_dotenv
import os
import requests
#from pykrx import stock
import datetime as dt
import openpyxl
import math
import random
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
import re
import ta # 기술적 지표 계산 라이브러리



################ DEPENDENCIES ###########################

# pip install -r requirements.txt

#########################################################


################ PREDETERMINED FIELDS ###################

EMAIL = os.environ['EMAIL_ADDRESS']
PASSWORD = os.environ['EMAIL_PASSWORD']
# Get the API key
fmp_key = os.environ['FMP_API_KEY']
recipients = ['chs_3411@naver.com', 'eljm2080@gmail.com', 'hyungsukchoi3411@gmail.com']

NUM_THREADS = 2 #multithreading 
CUTOFF = 0
lee_kw_list = [ #2025 이재명 정부 예상 수혜주 
    "Software", #AI
    "Information", #AI
    "Resorts",
    "Casinos",
    "Energy",
    "Solar",
    "Wind",
    "Plant",
    "Construction",
    "Biotechnology",
]

country = 'KR'
limit=200 # 250 requests/day
sp500 = True

#########################################################



# print('May take up to few minutes...')

today = dt.datetime.today().weekday()
weekend = today - 4 # returns 1 for saturday, 2 for sunday
formattedDate = (dt.datetime.today() - dt.timedelta(days = weekend)).strftime("%Y%m%d") if today >= 5 else dt.datetime.today().strftime("%Y%m%d")

three_months_approx = dt.datetime.today() - dt.timedelta(days=90)
formattedDate_3m_ago =  three_months_approx.strftime("%Y%m%d")

# dfKospi = stock.get_market_fundamental(formattedDate, market="ALL")

data = []
data_lock = threading.Lock()

# Load environment variables from .env file
#load_dotenv()


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

def get_tickers_by_country(country: str, limit: int, apikey: str):
    url = 'https://financialmodelingprep.com/api/v3/stock-screener'
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/114.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'apikey': apikey,
    }
    
    params = {
        'country': country,
        'limit': limit,
        'type': 'stock',
        'sort': 'marketCap',
        'order': 'desc',
        'apikey': apikey,
        'isEtf': False,
        'isFund': False,
        # 'sector' : Consumer Cyclical | Energy | Technology | Industrials | Financial Services | Basic Materials | Communication Services | Consumer Defensive | Healthcare | Real Estate | Utilities | Industrial Goods | Financial | Services | Conglomerates
        # 'exchange' : nyse | nasdaq | amex | euronext | tsx | etf | mutual_fund
    }
    try:
        response = requests.get(url, params=params, headers=headers)
    except Exception as e:
        print('FMP error:', e)
        return []
    data = response.json()
    return [item['symbol'] for item in data]

# buffett's philosophy & my quant ideas
def buffett_score (de, cr, pbr, per, ind_per, roe, ind_roe, roa, ind_roa, eps, div, icr, opinc_yoy, opinc_qoq):
    score = 0
    #basic buffett-style filtering
    if de is not None and de <= 0.5 and de != 0:
        score +=1
    if cr is not None and (cr >= 1.5 and cr <= 2.5):
        score +=1

    if pbr is not None and (pbr <= 2 and pbr != 0):
        score +=0.5
        if pbr <= 1.5:
            score +=1
            if pbr <= 1:
                score += 0.5
        

    # 고배당주 수혜 예상
    # if div is not None: #cagr = +4~6-10%
    #     if div >= 0.1:
    #         score +=1.0
    #     elif div >= 0.08:
    #         score +=0.75
    #     elif div >= 0.06:
    #         score +=0.5
    if div: #3y yoy
        score +=1
    
    if opinc_yoy: #3y yoy
        score +=1
    if opinc_qoq: #5q qoq
        score +=0.5

    if eps is True:
        score += 1
    if eps is False:
        score -= 1
    
    if not isinstance(eps, bool) and eps is not None:
        if eps >= 0.1:
            score += 1
        if eps < 0:
            score -= 1
        if eps > 0 and per is not None:
            peg = per / (eps * 100) #peg ratio, underv if less than 1
            if peg <= 1:
                score += 1

    if icr is not None and icr >= 5: #x5
        score +=1

    #my quant ideas 
    if eps is not None:
        #  3. 고배당 + 고EPS 성장률 전략 (배당 성장주 전략)
        # 아이디어: 고배당이면서 실적 성장세가 뚜렷한 기업
        if div and eps >= 0.3:
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
    
def get_trading_volume(ticker):
    # 1) 데이터 가져오기
    df = stock.get_market_trading_volume_by_date(formattedDate_3m_ago, formattedDate, ticker[:6])

    # 2) 외국인·기관 동시 순매수일 수 계산
    df['기관_순매수_양수'] = df['기관합계'] > 0
    df['외국인_순매수_양수'] = df['외국인합계'] > 0
    df['동시_순매수'] = df['기관_순매수_양수'] & df['외국인_순매수_양수']
    simultaneous_buy_days = df['동시_순매수'].sum()

    return simultaneous_buy_days


def get_per_krx(ticker):
    url = f"https://finance.naver.com/item/main.naver?code={ticker[:6]}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Referer": "https://finance.naver.com/",
        "Connection": "keep-alive"
    }
    session = requests.Session()
    session.headers.update(headers)

    
    try:
        # 첫 요청으로 쿠키 확보 (홈페이지 접속)
        session.get("https://finance.naver.com/", timeout=3)
        res = session.get(url, timeout=3)
        time.sleep(random.uniform(0.7, 1.8)) # 딜레이 필수
        # Sleep for a random time to mimic human behavior
        res.raise_for_status()  # Optional: raises an error for HTTP issues
    except requests.exceptions.HTTPError as e:
        if res.status_code == 401:
            print("Unauthorized (401) - You might need to log in or use a valid token.")
        else:
            print(f"HTTP error occurred: {e} (Status Code: {res.status_code})")
    except requests.RequestException as e:
        print(f"Request failed: {e}")

    soup = BeautifulSoup(res.text, 'html.parser')

    data = {'name':(None, None), 'PBR': None, 'IND_PER': None, 'PER': None, 'DPS YoY': None, 'ROE': None, "IND_ROE": None, "OpIncY": None, "OpIncQ": None}

    # 종목명
    name_tag = soup.select_one("div.wrap_company h2")
    name = name_tag.text.strip() if name_tag else None

    # 업종명 전체 텍스트
    sector_tag = soup.select_one("#content > div.section.trade_compare > h4 > em")
    sector_text = sector_tag.text.strip() if sector_tag else None

    sector = None
    if sector_text:
        # 정규식으로 '업종명 : (내용)｜' 패턴에서 (내용)만 추출
        match = re.search(r"업종명\s*:\s*(.+?)\s*｜", sector_text)
        if match:
            sector = match.group(1).strip()
        else:
            # 만약 구분자 '｜'가 없으면 '업종명 :' 뒤부터 끝까지 가져오기
            sector = sector_text.split("업종명 :")[-1].strip()

    data['name'] = (name, sector)
    ####
    aside = soup.select_one('div.aside_invest_info')
    if aside:
        rows = aside.select('table tr')
        if rows:
            for row in rows:
                text = row.text
                em = row.select_one('td em')
                if not em:
                    continue
                per_text = em.text.strip()

                if 'PBR' in text:
                    data['PBR'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None

                elif '동일업종 PER' in text:
                    data['IND_PER'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None

                elif 'PER' in text and 'EPS' in text and '추정PER' not in text:
                    data['PER'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None
    
    # DPS 계산
    ##############################################################
    table = soup.select_one('div.section.cop_analysis table')
    if table:
        dividend = []
        rows = table.select('tbody tr')
        if rows:
            for row in rows:
                th = row.find('th')
                if th and '주당배당금' in th.text:
                    tds = row.select('td')
                    if not tds:
                        continue
                    for td in tds:
                        val = td.text.strip().replace(',', '').replace('원', '')
                        try:
                            dividend.append(float(val))
                        except (ValueError, TypeError):
                            dividend.append(None)
                    break  # Found and processed the DPS row

        # Filter out None values and take first 3
        first_three = dividend[:3]
        first_three = list(filter(lambda x: x is not None, first_three))

        # Only compare if we have at least 2 values
        if len(first_three) >= 2:
            data['DPS YoY'] = all(
                earlier <= later for earlier, later in zip(first_three, first_three[1:])
            )
    #Operating Income YoY
    ##############################################################
    table = soup.select_one('div.section.cop_analysis table')
    if table:
        opinc = []
        rows = table.select('tbody tr')
        if rows:
            for row in rows:
                th = row.find('th')
                if th and '영업이익률' in th.text:
                    tds = row.select('td')
                    if not tds:
                        continue
                    for td in tds:
                        val = td.text.strip().replace(',', '').replace('원', '')
                        try:
                            opinc.append(float(val))
                        except (ValueError, TypeError):
                            opinc.append(None)
                    break  # Found and processed the DPS row

        # Filter out None values and take first 3
        yoy = opinc[:3]
        yoy = list(filter(lambda x: x is not None, yoy))

        qoq = opinc[4:9]
        qoq = list(filter(lambda x: x is not None, qoq))

        # Only compare if we have at least 2 values
        if len(yoy) >= 2:
            data['OpIncY'] = all(
                earlier <= later for earlier, later in zip(yoy, yoy[1:])
            )
        if len(qoq) >= 2:
            data['OpIncQ'] = all(
                earlier <= later for earlier, later in zip(qoq, qoq[1:])
            )
    ########################

    # 동일업종 비교 테이블은 div.section.inner_sub > table.class="compare" 내부에 위치
    compare_table = soup.select_one('div.section.trade_compare table')

    if compare_table:
        rows = compare_table.select('tr')
        if rows:
            for row in rows:
                th = row.find('th')
                if th and 'ROE' in th.text:
                    tds = row.find_all('td')
                    if not tds:
                        continue  # No data to process

                    # Extract text and clean %
                    result = [td.text.strip().replace('%', '') for td in tds]

                    # Parse company ROE
                    try:
                        if result and result[0] != '':
                            data['ROE'] = float(result[0])
                    except (ValueError, IndexError):
                        data['ROE'] = None  # Redundant due to default, but explicit

                    # Parse industry ROE values
                    raw_industry_values = result[1:] if len(result) > 1 else []
                    cleaned_values = []

                    for item in raw_industry_values:
                        try:
                            if item != '':
                                cleaned_values.append(float(item))
                        except ValueError:
                            continue

                    cleaned_values = list(filter(lambda x: x >= -20, cleaned_values)) #clean outliers

                    if cleaned_values:
                        data['IND_ROE'] = sum(cleaned_values) / len(cleaned_values)

                    break  # Only process the first ROE row

    return data

# def has_stable_dividend_growth(ticker):
#     stock = yf.Ticker(ticker)
#     divs = stock.dividends
#     # Ensure we have at least 10 years of data
#     if divs.empty:
#         return False

#     # Get annual total dividends for the past 10 years
#     annual_divs = divs.groupby(divs.index.year).sum()
#     if len(annual_divs) < 10:
#         return False
    
#     recent_years = sorted(annual_divs.index)[-11:-1] # returns [last year - 9 = 2015, 2016, ..., last year = 2024], # use -11 to start around 10 years ago from now

#     if recent_years[0] < dt.datetime.today().year - 12: # sift out old data
#         return False

#     last_10_divs = [annual_divs[year] for year in recent_years]
#     # print(last_10_divs)

#     # Check for stable or increasing dividends
#     tolerance = 0.85 # tolerance band to account for crises and minor dividend cuts
#     return all(earlier * tolerance <= later for earlier, later in zip(last_10_divs, last_10_divs[1:])) # zip returns [(2015div, 2016div), (2016div, 2017div), ..., (2024div, 2025div)]
    
'''
def has_stable_dividend_growth_cagr(ticker):

    stock = yf.Ticker(ticker)
    divs = stock.dividends
    # Ensure we have at least 10 years of data
    if divs.empty:
        return None

    # Get annual total dividends for the past 10 years
    annual_divs = divs.groupby(divs.index.year).sum()
    if len(annual_divs) < 10:
        return None
    
    recent_years = sorted(annual_divs.index)[-11:-1] # returns [last year - 9 = 2015, 2016, ..., last year = 2024], # use -11 to start around 10 years ago from now

    if dt.datetime.today().year - 1 not in recent_years: # sift out old data
        return None
    
    last_10_divs = [annual_divs[year] for year in recent_years]

    div_start = last_10_divs[0]
    div_end = last_10_divs[-1]
    if len(last_10_divs) == 0 or div_start == 0:
        return None
    else:
        cagr = ((div_end / div_start) ** (1/len(last_10_divs))) - 1
        return cagr
'''

# def has_stable_eps_growth(ticker):
#     ticker = yf.Ticker(ticker)

#     # Get annual income statement
#     income_stmt = ticker.financials # Annual by default

#     # Make sure EPS is in the statement
#     if "Diluted EPS" in income_stmt.index:
#         eps_series = income_stmt.loc["Diluted EPS"]
#         if dt.datetime.today().year - 6 in eps_series.index.year:
#             return False
#         eps_list = eps_series.sort_index().dropna().tolist() # Sorted from oldest to newest
#         tolerance = 0.9
#         return all(earlier * tolerance <= later for earlier, later in zip(eps_list, eps_list[1:]))
#     else:
#         return False


# def has_stable_eps_growth_quarterly(ticker):
#     ticker = yf.Ticker(ticker)

#     # Get quarterly earnings data (contains actual EPS in 'Earnings' column)
#     quarterly_eps = ticker.quarterly_earnings

#     # Make sure there is enough data
#     if quarterly_eps is None or quarterly_eps.empty or len(quarterly_eps) < 8:
#         return False

#     # Sort by date ascending (oldest first)
#     quarterly_eps = quarterly_eps.sort_index()

#     eps_list = quarterly_eps['Earnings'].dropna().tolist()

#     # Define tolerance for stable growth (e.g., each quarter at least 90% of previous)
#     tolerance = 0.9

#     # Check stable growth: every EPS >= 90% of previous EPS
#     return all(earlier * tolerance <= later for earlier, later in zip(eps_list, eps_list[1:]))

def has_stable_eps_growth_cagr(ticker):
    ticker = yf.Ticker(ticker)

    # Get annual income statement
    income_stmt = ticker.financials # Annual by default

    # Make sure EPS is in the statement

    try:
        if "Diluted EPS" in income_stmt.index:
            eps_series = income_stmt.loc["Diluted EPS"]
            if dt.datetime.today().year - 1 not in eps_series.index.year:
                return None
            eps_list = eps_series.sort_index().dropna().tolist() # Sorted from oldest to newest
            eps_start = eps_list[0]
            eps_end = eps_list[-1]
            if len(eps_list) == 0:
                return None
            if eps_start <= 0 or eps_end < 0:
                return all(earlier <= later for earlier, later in zip(eps_list, eps_list[1:]))
            else:
                cagr = ((eps_end / eps_start) ** (1/len(eps_list))) - 1
                return cagr
        else:
            return None
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

# def bvps_undervalued(bvps, current):
#     if not bvps:
#         return False
#     if bvps > current:
#         return True #undervalued
#     else:
#         return False

# def has_stable_book_value_growth(ticker, sector: str):
#     ticker = yf.Ticker(ticker)

#     # Get annual balance sheet
#     balance_sheet = ticker.balance_sheet # Columns are by period (most recent first)

#     # Reverse columns to go oldest → newest
#     balance_sheet = balance_sheet.iloc[:, ::-1]
#     book_values = []

#     for date in balance_sheet.columns:
#         if date.year < dt.datetime.today().year - 6: # sift out old data
#             return False
        
#         try:
#             book_value = balance_sheet.loc["Common Stock Equity", date]
#             outstanding_shares = balance_sheet.loc["Ordinary Shares Number", date]
#             if math.isnan(book_value) or math.isnan(outstanding_shares) or not outstanding_shares:
#                 continue
#             else:
#                 bvps = book_value / outstanding_shares 
#                 book_values.append(round(bvps, 2))
#         except Exception as e:
#             continue
            
#     if len(book_values) < 2:
#         return False
    
#     tolerance = 0.85 if sector in {'Industrials', 'Technology', 'Energy', 'Consumer Cyclical', 'Basic Materials'} else 0.9 #set is faster than list in checking O(1) avg
#     return all(earlier * tolerance <= later for earlier, later in zip(book_values, book_values[1:]))

# def get_esg_score(ticker):
#     ans = ''
#     ticker = yf.Ticker(ticker)
#     esg = ticker.sustainability
#     try:
#         sust = esg.loc['totalEsg', 'esgScores']
#         rateY = esg.loc['esgPerformance', 'esgScores']
#         ans = str(sust) + ', ' + str(rateY)
#     except Exception:
#         return ans
#     finally:
#         return ans

def get_percentage_change(ticker):
    ticker = yf.Ticker(ticker)

    # Get last 2 days of price data
    data = ticker.history(period="2d")

    # Check if we have at least 2 days and prev_close is not zero
    if len(data) >= 2:
        prev_close = data['Close'].iloc[-2]
        last_close = data['Close'].iloc[-1]

        if prev_close != 0:
            percent_change = ((last_close - prev_close) / prev_close) * 100
            if percent_change is None:
                return None
            else:
                if percent_change >= 0:
                    return (f" (+{percent_change:.2f}%)")  # e.g., (-6.20%)
                else:
                    return (f" ({percent_change:.2f}%)")  # e.g., (-6.20%)
        else:
            return ' ()'
    else:
        return ' ()'

# # FullRatio의 산업별 PER 페이지 URL
# url = 'https://fullratio.com/pe-ratio-by-industry'
# headers = {'User-Agent': 'Mozilla/5.0'}

# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.text, 'html.parser')

# # 테이블 찾기 (이때 table이 None인지 체크)
# table = soup.find('table')
# if table is None:
#     raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

# # tbody가 있는 경우
# tbody = table.find('tbody')
# if tbody:
#     rows = tbody.find_all('tr')
# else:
#     rows = table.find_all('tr')[1:] # 헤더 제외

# # 각 행에서 데이터 추출
# per_data = []
# for row in rows:
#     cols = row.find_all('td')
#     if len(cols) >= 2:
#         industry = cols[0].text.strip()
#         pe_ratio = cols[1].text.strip()
#         per_data.append({'Industry': industry, 'P/E Ratio': pe_ratio})

# # 결과 출력
# df_per = pl.DataFrame(per_data)

# url_roe = 'https://fullratio.com/roe-by-industry'
# headers_roe = {'User-Agent': 'Mozilla/5.0'}

# response_roe = requests.get(url_roe, headers=headers_roe)
# soup_roe = BeautifulSoup(response_roe.text, 'html.parser')

# # 테이블 찾기 (이때 table이 None인지 체크)
# table_roe = soup_roe.find('table')
# if table_roe is None:
#     raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

# # tbody가 있는 경우
# tbody_roe = table_roe.find('tbody')
# if tbody_roe:
#     rows_roe = tbody_roe.find_all('tr')
# else:
#     rows_roe = table_roe.find_all('tr')[1:] # 헤더 제외

# # 각 행에서 데이터 추출
# roe_data = []
# for row in rows_roe:
#     cols_roe = row.find_all('td')
#     if len(cols_roe) >= 2:
#         industry_roe = cols_roe[0].text.strip()
#         roe_num = cols_roe[1].text.strip()
#         roe_data.append({'Industry': industry_roe, 'ROE': roe_num})

# # 결과 출력
# df_roe = pl.DataFrame(roe_data)
# #
# #
# url_roa = 'https://fullratio.com/roa-by-industry'
# headers_roa = {'User-Agent': 'Mozilla/5.0'}

# response_roa = requests.get(url_roa, headers=headers_roa)
# soup_roa = BeautifulSoup(response_roa.text, 'html.parser')

# # 테이블 찾기 (이때 table이 None인지 체크)
# table_roa = soup_roa.find('table')
# if table_roa is None:
#     raise Exception("테이블을 찾을 수 없습니다. 구조가 바뀌었거나 JS로 로딩될 수 있습니다.")

# # tbody가 있는 경우
# tbody_roa = table_roa.find('tbody')
# if tbody_roa:
#     rows_roa = tbody_roa.find_all('tr')
# else:
#     rows_roa = table_roa.find_all('tr')[1:] # 헤더 제외

# # 각 행에서 데이터 추출
# roa_data = []
# for row in rows_roa:
#     cols_roa = row.find_all('td')
#     if len(cols_roa) >= 2:
#         industry_roa = cols_roa[0].text.strip()
#         roa_num = cols_roa[1].text.strip()
#         roa_data.append({'Industry': industry_roa, 'ROA': roa_num})

# df_roa = pl.DataFrame(roa_data)
# #

def get_industry_roe(ind):
    return 0.1
    # if country is None:
    #     try:
    #         if ind is not None:
    #             ans = float(df_roe.filter(pl.col('Industry') == ind).select("ROE").item())
    #             return ans/100.0
    #         else:
    #             return 0.08
    #     except Exception:
    #         return 0.08 
    # else:
    #     return 0.1

def get_industry_roa(ind):
    if any(kw in ind for kw in ['Insurance', 'Bank']):
        return 0.01
    else:
        return 0.05
    # if country is None:
    #     try:
    #         if ind is not None:
    #             ans = float(df_roa.filter(pl.col('Industry') == ind).select("ROA").item())
    #             return ans/100.0
    #         return 0.06
    #     except Exception:
    #         return 0.06
    # elif country == 'KR' and any(kw in ind for kw in ['Insurance', 'Bank']):
    #     return 0.01
    # else:
    #     return 0.05

    

# def get_industry_per(ind, ticker):
#     if country is None: #country == US
#         spy = yf.Ticker('SPY')
#         spy_info = spy.info
#         per = spy_info.get('trailingPE')
#         try: 
#             if ind is not None:
#                 ans = float(df_per.filter(pl.col('Industry') == ind).select("P/E Ratio").item())
#                 return ans
#             return per
#         except Exception:
#             return per
#     elif country == 'KR':
#         try:
#             url = f"https://finance.naver.com/item/main.nhn?code={ticker[:6]}"
#             headers = {'User-Agent': 'Mozilla/5.0'}
#             res = requests.get(url, headers=headers)
#             soup = BeautifulSoup(res.text, 'html.parser')

#             # 동일업종 PER이 들어있는 박스 찾기
#             aside = soup.select_one('div.aside_invest_info')
#             if aside:
#                 rows = aside.select('table tr')
#                 for row in rows:
#                     if '동일업종 PER' in row.text:
#                         per_text = row.select_one('td em').text
#                         return float(per_text.replace(',', ''))
#             return None
#         except Exception:
#             return None

#     elif country == 'JP':
#         ewj = yf.Ticker('EWJ')
#         info = ewj.info
#         per = info.get('trailingPE')
#         return per
#     else:
#         vt = yf.Ticker('VT')
#         info = vt.info
#         per = info.get('trailingPE')
#         return per


######## LOAD TICKERS ###########
raw_tickers = get_tickers(country, limit, sp500)

filtered = list(filter(lambda x: isinstance(x, str), raw_tickers))


# block of code that gets rid of preferred stocks
prohibited = {'008560.KS', '003550.KS', '048260.KQ', '000060.KS', '091990.KQ', '066970.KQ', '022100.KQ', '010145.KS', '003410.KS', '086520.KQ', '087010.KQ', '000250.KQ'}
def keep_ticker(t):
    return len(t) > 5 and t[5] == '0' and t not in prohibited

tickers = list(filter(keep_ticker, filtered))


# tickers = [
#     '005930.KS',  # Samsung Electronics
#     '000660.KS',  # SK Hynix
#     '035420.KS',  # Naver
#     '207940.KQ',  # Samsung Biologics
#     '051910.KS',  # LG Chem
#     '068270.KS',  # Celltrion
#     '005380.KS',  # Hyundai Motor
#     '035720.KQ',  # Kakao
#     '055550.KS',  # Shinhan Financial Group
#     '012330.KS',  # Hyundai Mobis
#     '105560.KS',  # KB Financial Group
#     '036570.KS',  # NCSoft
#     '017670.KS',  # SK Telecom
#     '015760.KS',  # Korean Electric Power
#     '096770.KS',  # SK Innovation
#     '000270.KS',  # Kia Corporation
#     '003550.KS',  # LG
#     '033780.KS',  # KT&G
#     '006400.KS',  # Samsung SDI
#     '010130.KS',  # Samsung Electronics Engineering
#     '000810.KS',  # Samsung C&T
#     '091990.KQ',  # Celltrion Healthcare
#     '014680.KS',  # S-Oil
#     '004020.KS',  # Hyundai Heavy Industries
#     '035250.KQ',  # Kakao Games
#     '010950.KS',  # S-Oil
#     '041510.KS',  # LG Household & Health Care
#     '034020.KS',  # LG Display
#     '015020.KS',  # POSCO
#     '011170.KS'   # Lotte Chemical
# ]


###################################################################
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
        # 데이터 다운로드 (auto_adjust=True 유지)
        df_momentum = yf.download(ticker, period='1y', interval='1d', progress=False, auto_adjust=True)

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

        df_momentum['MA50'] = df_momentum['Close'].rolling(window=50).mean()
        df_momentum['MA200'] = df_momentum['Close'].rolling(window=200).mean()

        if pd.notna(df_momentum['MA50'].iloc[-1]) and pd.notna(df_momentum['MA200'].iloc[-1]):
            if df_momentum['MA50'].iloc[-1] > df_momentum['MA200'].iloc[-1]:
                result['ma_crossover_lt'] = True


        # 20일 수익률 계산
        try:
            return_20d = (df_momentum['Close'].iloc[-1] / df_momentum['Close'].iloc[-21] - 1) * 100
            if return_20d >= 10:
                result['return_20d'] = True
        except IndexError:
            print(f"[Warning] Not enough data for 20-day return calculation for {ticker}")

        # 60일 수익률 계산
        try:
            return_60d = (df_momentum['Close'].iloc[-1] / df_momentum['Close'].iloc[-61] - 1) * 100
            if return_60d >= 10:
                result['return_60d'] = True  # 필요하면 키 이름도 'return_60d'로 변경 가능
        except IndexError:
            print(f"[Warning] Not enough data for 60-day return calculation for {ticker}")


        try:
            rsi = ta.momentum.RSIIndicator(df_momentum['Close'], window=14).rsi()
            # print("RSI tail:\n", rsi.tail(5))  # 값 확인용 출력

            if len(rsi) >= 2 and pd.notna(rsi.iloc[-2]) and pd.notna(rsi.iloc[-1]):
                if (
    (rsi.iloc[-2] < 40 and rsi.iloc[-1] > rsi.iloc[-2]) or
    (30 <= rsi.iloc[-1] <= 60 and rsi.iloc[-1] > rsi.iloc[-2]) or
    (rsi.iloc[-2] < 50 and rsi.iloc[-1] >= 50)):
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
        res = check_momentum_conditions(ticker)
        res['Ticker'] = ticker
        results.append(res)
    # 결과 리스트를 DataFrame으로 변환 (Ticker 컬럼 첫 칼럼으로 이동)
    df_results = pd.DataFrame(results)
    cols = ['Ticker'] + [c for c in df_results.columns if c != 'Ticker']
    df_results = df_results[cols]
    return df_results

df_batch_result = check_momentum_conditions_batch(tickers)
###################################################################


# def get_momentum_batch(tickers, period_months=12):
#     try:
#         data = yf.download(tickers, period="3y", interval="1mo", progress=False, auto_adjust=True)['Close']
#     except Exception:
#         return {}

#     momentum_dict = {}
#     for ticker in tickers:
#         if ticker not in data.columns:
#             momentum_dict[ticker] = None
#             continue
#         prices = data[ticker].dropna()
#         if len(prices) < period_months:
#             momentum_dict[ticker] = None
#             continue
#         momentum = (prices.iloc[-1] / prices.iloc[-period_months]) - 1
#         momentum_dict[ticker] = momentum

#     return momentum_dict

# momentum_6m = get_momentum_batch(tickers, 6)
# momentum_1y = get_momentum_batch(tickers, 12)
# momentum_3y = get_momentum_batch(tickers, 36)

# def momentum_score(short, mid, long):
   
#     def score_momentum(mom, good_thresh, bad_thresh):
#         if mom is None:
#             return 0
#         if mom >= good_thresh:
#             return 1
#         elif mom <= bad_thresh:
#             return -1
#         else:
#             return 0
    
#     weights = {
#     'short': 0.15,
#     'mid': 0.35,
#     'long': 0.5
# }

#     thresholds = {
#     'short': (0.2, 0.0),   # +3% / -3% over 6 months
#     'mid': (0.4, 0.0),     # +5% / -4% over 1 year
#     'long': (0.6, 0.0)       # +20% / 0% over 3 years
# }

    
#     total_score = 0
#     total_score += score_momentum(short, *thresholds['short']) * weights['short']
#     total_score += score_momentum(mid, *thresholds['mid']) * weights['mid']
#     total_score += score_momentum(long, *thresholds['long']) * weights['long']
    
#     return round(total_score,2)

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
            krx_per = get_per_krx(ticker[:6])

            info = yf.Ticker(ticker).info
            name = krx_per['name'][0]
            industry = krx_per['name'][1]
            currentPrice = info.get("currentPrice", None)
            percentage_change = get_percentage_change(ticker)
            # target_mean = info.get('targetMeanPrice', 0)
            # if target_mean != 0 and currentPrice != 0 and currentPrice is not None and target_mean is not None:
            #     target_incr = ((target_mean - currentPrice) / currentPrice) * 100
            #     upside = str(round(target_incr)) + '%' if target_incr < 0 else '+' + str(round(target_incr)) + '%'
            # else: 
            #     upside = 'N/A'
            
            debtToEquity = info.get('debtToEquity', None) # < 0.5
            debtToEquity = debtToEquity/100 if debtToEquity is not None else None
            currentRatio = info.get('currentRatio', None) # 초점: 회사의 단기 유동성, > 1.5 && < 2.5

            pbr = krx_per['PBR'] # 주가가 그 기업의 자산가치에 비해 과대/과소평가되어 있다는 의미. 낮으면 자산활용력 부족
            per = krx_per['PER'] # high per expects future growth but could be overvalued(=버블). 
                                                                       # low per could be undervalued or company in trouble, IT, 바이오 등 성장산업은 자연스레 per이 높게 형성
            if per is None:
                per = info.get('trailingPE', None)                                                           # 저per -> 수익성 높거나 주가가 싸다 고pbr -> 자산은 적은데 시장에서 비싸게 봐준다
            industry_per = krx_per['IND_PER'] 
            industry_per = round(industry_per) if industry_per is not None else industry_per

            industry_roe = krx_per['IND_ROE']
            industry_roa = get_industry_roa(industry)

            roe = krx_per['ROE'] # 수익성 높은 기업 선별. 고roe + 저pbr 조합은 가장 유명한 퀀트 전략. > 8% (0.08) 주주 입장에서 수익성
            if roe is None:
                roe = info.get('returnOnEquity', None)
            roa = info.get('returnOnAssets', None) # > 6% (0.06), 기업 전체 효율성
            #ROE가 높고 ROA는 낮다면? → 부채를 많이 이용해 수익을 낸 기업일 수 있음. ROE와 ROA 모두 높다면? → 자산과 자본 모두 효율적으로 잘 운용하고 있다는 의미.
            #A = L + E
            
            eps_growth = has_stable_eps_growth_cagr(ticker) # earnings per share, the higher the better, buffett looks for stable EPS growth
            # eps_growth_quart = has_stable_eps_growth_quarterly(ticker) 
            div_growth = krx_per['DPS YoY'] # buffett looks for stable dividend growth for at least 10 years
            # bvps_growth = bvps_undervalued(info.get('bookValue', None), currentPrice)
            operating_income_yoy = krx_per['OpIncY']
            operating_income_qoq = krx_per['OpIncQ']
            icr = get_interest_coverage_ratio(ticker)
            
            # try:
            #     short_momentum = momentum_6m[ticker]
            # except KeyError:
            #     short_momentum = None

            # try:
            #     mid_momentum = momentum_1y[ticker]
            # except KeyError:
            #     mid_momentum = None

            # try:
            #     long_momentum = momentum_3y[ticker]
            # except KeyError:
            #     long_momentum = None
            
            ma = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'ma_crossover'].values[0]
            ma_lt = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'ma_crossover_lt'].values[0]
            ret20 = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'return_20d'].values[0]
            ret60 = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'return_60d'].values[0]
            rsi = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'rsi_rebound'].values[0]
            macd = df_batch_result.loc[df_batch_result['Ticker'] == ticker, 'macd_golden_cross'].values[0]

            momentum_score = score_momentum(ma, ma_lt, ret20, ret60, rsi, macd)
            vol = get_trading_volume(ticker)
            cyclicality = 0
            # ACTIVATE THE CODE BELOW TO SCORE CYCLICALITY DEPENDING ON CURRENT MACROECON SITUATION
            # classification = classify_cyclicality(industry)
            # if classification == 'defensive':
            #     cyclicality +=1
            # elif classification == 'cyclical':
            #     cyclicality -=0.
            
            '''
            if industry is not None:
                if any(kw in industry for kw in lee_kw_list):
                    cyclicality += 1
            '''


            quantitative_buffett_score = buffett_score(debtToEquity, currentRatio, pbr, per, industry_per, roe, industry_roe, roa, industry_roa, eps_growth, div_growth, icr, operating_income_yoy, operating_income_qoq) + cyclicality
            # quantitative_buffett_score = buffett_score(debtToEquity, currentRatio, pbr, per, industry_per, roe, industry_roe, roa, industry_roa, eps_growth, div_growth, icr) + cyclicality

            # rec = info.get('recommendationKey', None)
            # if country is None:
            #     esg = get_esg_score(ticker)
            # else:
            #     esg = ''

            ## FOR extra 10 score:::
            # MOAT -> sustainable competitive advantage that protects a company from its competitors, little to no competition, dominant market share, customer loyalty 
            # KEY: sustainable && long-term durability
            # ex) brand power(Coca-Cola), network effect(Facebook, Visa), cost advantage(Walmart, Costco), high switching costs(Adobe),
            # regulatory advantage(gov protection), patients(Pfizer, Intel)
            
            roe_print = f'{round(roe,1)}%' if roe is not None else 'N/A'
            roe_print += f'({round(industry_roe)})' if industry_roe is not None else ''

            per_print = f'{round(per,2)}' if per is not None else 'N/A'
            per_print += f'({industry_per})' if industry_per is not None else ''

            result = {
                "티커": ticker[:6] if country == 'KR' else ticker,
                "종목": name,
                "B-Score": round(quantitative_buffett_score, 1),
                "업종": industry,
                "주가(전날대비)": f"{currentPrice:,.0f}" + percentage_change if country == 'KR' or country == 'JP' else f"{currentPrice:,.2f}" + percentage_change,
                "부채비율": round(debtToEquity, 2) if debtToEquity is not None else 'N/A',
                "유동비율": round(currentRatio, 2) if currentRatio is not None else 'N/A',
                "PBR": round(pbr,2) if pbr is not None else None,
                "PER(업종)": per_print,
                "ROE(업종)": roe_print,
                "ROA": str(round(roa*100,1)) + '%' if roa is not None else 'N/A',
                "ICR": round(icr,1) if icr is not None else 'N/A',
                "EPS성장률": eps_growth if isinstance(eps_growth, bool) else (f"{eps_growth:.2%}" if eps_growth is not None else 'N/A'), #use this instead of operating income incrs for quart/annual 
                # "배당 성장률": f"{div_growth:.2%}" if div_growth is not None else None,
                "배당안정성": div_growth if div_growth is not None else 'N/A',
                "영업이익률": operating_income_yoy if operating_income_yoy is not None else 'N/A',
                '모멘텀': momentum_score,
                '거래량': vol,
                # 'Analyst Forecast': rec + '(' + upside + ')',
                #모멘텀(6m/1y/3y)': "/".join(f"{m:.1%}" if m is not None else "None" for m in (short_momentum, mid_momentum, long_momentum)),
                # 'ESG': esg, #works only for US stocks
            }

            if quantitative_buffett_score >= CUTOFF:
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
            # data.append({
            #     "Ticker": ticker,
            #     "Name": '',
            #     "Industry": '',
            #     "Price": '',
            #     "D/E": 0,
            #     "CR": 0,
            #     "PBR": 0,
            #     "PER": 0,
            #     "ROE": 0,
            #     "ROA": 0,
            #     "ICR": 0,
            #     "EPS CAGR": '',
            #     "DIV CAGR": '',
            #     "B-Score": 0.0,
            #     'Analyst Forecast': '',
            #     'Momentum': '',
            #     'ESG': '',
            # })

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

# Find the maximum B-Score
max_b_score = df["B-Score"].max()
df["B-Score"] = (df["B-Score"] / max_b_score) * 100
# Round the B-Score values to 1 decimal place
df["B-Score"] = df["B-Score"].round(0)

# 거래량 정규화 및 반올림
max_volume = df["거래량"].max()
df["거래량"] = (df["거래량"] / max_volume) * 100
df["거래량"] = df["거래량"].round(0)

# 모멘텀 정규화 및 반올림
max_momentum = df["모멘텀"].max()
df["모멘텀"] = (df["모멘텀"] / max_momentum) * 100
df["모멘텀"] = df["모멘텀"].round(0)

df["합계점수"] = df["B-Score"] + df["거래량"] + df["모멘텀"]

df = df.sort_values(by='B-Score', ascending=False)

if country: 

    filename = f"result_{country}_{formattedDate}.xlsx"

    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']

        # Define column widths you want (by column name)
        col_widths = {
            '종목': 25,
            '업종': 20,
            '주가(전날대비)': 15,
            'EPS성장률': 10,
            '배당안정성': 10,
            '영업이익률': 10,
            #'모멘텀(6m/1y/3y)': 21,
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
            'style': 'Table Style Medium 9'  # You can choose different table styles
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

        # 노란색 조건 (PBR > 3)
        worksheet.conditional_format(pbr_range, {
            'type': 'cell',
            'criteria': '>',
            'value': 3,
            'format': yellow_format
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
                
                if col_name in ['PER(업종)', 'ROE(업종)', 'ROA', '부채비율', '유동비율', 'ICR']:
                    fmt = right_align_format
                elif col_name in ['EPS성장률', '배당안정성', '영업이익률']:
                    fmt = center_align_format
                else:
                    fmt = None

                worksheet.write(row_num, col_num, cell_value, fmt)



elif sp500:
    df.to_excel(f"s&p500_{formattedDate}.xlsx", index=False)
else:
    df.to_excel(f"nasdaq100_{formattedDate}.xlsx", index=False)

##########################################################################################################
time.sleep(3)

excel_path = f'result_KR_{formattedDate}.xlsx'

date_kr = dt.datetime.strptime(formattedDate, '%Y%m%d').strftime('%Y년 %m월 %d일')

msg = EmailMessage()
msg['Subject'] = f'재무 퀀트 리포트 | {date_kr}'
msg['From'] = Address(display_name='Hyungsuk Choi', addr_spec=EMAIL)
msg['To'] = ''  # or '' or a single address to satisfy the 'To' header requirement

content = (
    f"귀하의 투자 참고를 위해 {date_kr} 기준, "
    f"시가총액 상위 {limit}개 상장기업에 대한 최신 퀀트 분석 자료를 전달드립니다. "
    "각 기업의 종합 점수는 ‘B-Score’ 항목을 참고해 주시기 바라며, "
    "B-Score가 0점 미만인 기업은 자료에서 제외되었습니다.\n\n"
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
    "EPS 주당순이익 (Earnings Per Share): 1주당 기업이 창출한 순이익으로, 수익성과 성장성 판단에 유용합니다.\n"
    "배당안정성: 최근 3년간 배당의 지속성과 안정성을 평가한 지표입니다.\n"
    "영업이익률: 최근 3년간 평균 영업이익률 추세로, 기업의 수익성 수준을 보여줍니다.\n"
    "모멘텀: 주가 상승 흐름을 반영한 지표로, 주가의 탄력과 추세를 평가합니다.\n\n"
    "해당 메일은 매주 평일 오후 5시에 자동 발송되며, 안정적이고 현명한 투자를 위한 참고 자료로 제공됩니다.\n\n"
    "귀하의 성공적인 투자를 응원합니다."
)

msg.set_content(content)
html_content = f"""

<html>
  <body>
    <p>귀하의 투자 참고를 위해 <b>{date_kr}</b> 기준, 
    시가총액 상위 <b>{limit}</b>개 상장기업에 대한 최신 퀀트 분석 자료를 전달드립니다.</p>

    <p>각 기업의 종합 점수는 <b>B-Score</b> 항목을 참고해 주시기 바라며, 
    B-Score가 0점 미만인 기업은 자료에서 제외되었습니다.</p>

    <p>본 자료는 <b>워런 버핏의 투자 철학</b>을 기반으로, 기업의 재무 건전성을 수치화하여 평가한 결과입니다.<br>
    투자 판단 시에는 정성적 요소에 대한 별도의 면밀한 검토도 함께 병행하시기를 권장드립니다.</p>

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
        <tr><td><b>D/E</b></td><td>부채비율</td><td>자본 대비 부채의 비율로, 재무 건전성을 나타냅니다. 낮을수록 안정적입니다.</td></tr>
        <tr><td><b>CR</b></td><td>유동비율</td><td>유동자산이 유동부채를 얼마나 커버할 수 있는지를 보여줍니다.</td></tr>
        <tr><td><b>PBR</b></td><td>주가순자산비율</td><td>주가가 장부가치 대비 얼마나 높은지를 나타내며, 1보다 낮으면 저평가로 해석되기도 합니다.</td></tr>
        <tr><td><b>PER</b></td><td>주가수익비율</td><td>이익 대비 주가 수준을 나타냅니다. 낮을수록 이익 대비 저렴한 기업입니다.</td></tr>
        <tr><td><b>ROE</b></td><td>자기자본이익률</td><td>자본을(부채 미포함) 얼마나 효율적으로 운용해 이익을 냈는지를 나타냅니다.</td></tr>
        <tr><td><b>ROA</b></td><td>총자산이익률</td><td>총자산(부채 포함) 대비 수익률로, 보수적인 수익성 지표입니다.</td></tr>
        <tr><td><b>ICR</b></td><td>이자보상비율</td><td>영업이익으로 이자비용을 얼마나 감당할 수 있는지 나타냅니다.</td></tr>
        <tr><td><b>EPS</b></td><td>주당순이익</td><td>1주당 기업이 창출한 순이익으로, 수익성과 성장성 판단에 유용합니다.</td></tr>
        <tr><td><b>배당안정성</b></td><td>-</td><td>최근 3년간 배당의 지속성과 안정성을 평가한 지표입니다.</td></tr>
        <tr><td><b>영업이익률</b></td><td>-</td><td>최근 3년간 평균 영업이익률 추세로, 기업의 수익성 수준을 보여줍니다.</td></tr>
        <tr><td><b>모멘텀</b></td><td>-</td><td>주가 상승 흐름을 반영한 지표로, 주가의 탄력과 추세를 평가합니다.</td></tr>
      </tbody>
    </table>

    <p>해당 메일은 매주 평일 오후 5시에 자동 발송되며, 안정적이고 현명한 투자를 위한 참고 자료로 제공됩니다.</p>

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

