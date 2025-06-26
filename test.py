
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
import requests
from pykrx import stock
import datetime as dt
import openpyxl
import math
import random
from queue import Queue
import threading
import time
import polars as pl
import shelve
from bs4 import BeautifulSoup
from urllib.request import urlopen
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
import pandas as pd

import pandas as pd
import requests
import pandas as pd
import requests

def get_date_str(x):
    return x.split('(')[0].strip()

def get_finstate_naver(code, fin_type='0', freq_type='0'):
    url = f'https://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx?cmp_cd={code}&fin_typ={fin_type}&freq_typ={freq_type}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': f'https://finance.naver.com/item/main.nhn?code={code}'
    }
    
    resp = requests.get(url, headers=headers)
    resp.encoding = 'utf-8'
    
    if resp.status_code != 200:
        print(f"Request failed with status code {resp.status_code}")
        return None

    try:
        dfs = pd.read_html(resp.text)
    except Exception as e:
        print(f"Error parsing HTML: {e}")
        return None
    
    if len(dfs) == 0:
        print("No table found in the HTML response.")
        return None
    
    df = dfs[0]
    if df.empty or '해당 데이터가 존재하지 않습니다' in df.iloc[0,0]:
        print("No financial data found.")
        return None
    
    # 컬럼 이름 처리 (multiindex -> 단일 index)
    cols = []
    for col in df.columns:
        if isinstance(col, tuple):
            # 보통 ('', '2025.12(예상)') 이런 형태
            cols.append(get_date_str(col[1]))
        else:
            cols.append(col)
    
    cols[0] = 'date'
    df.columns = cols
    df.set_index('date', inplace=True)
    
    # 데이터 전치
    df_t = df.T
    
    # 인덱스를 datetime 형으로 변환 시도
    try:
        df_t.index = pd.to_datetime(df_t.index)
    except:
        pass
    
    # NaT 제거
    df_t = df_t[pd.notnull(df_t.index)]
    
    # 컬럼명 일부 수정
    df_t.rename(columns={'유보율': '자본유보율'}, inplace=True)
    df_t.rename(columns={'현금배당성향': '현금배당성향(%)'}, inplace=True)
    
    return df_t

# 테스트
code = '009830'  # 대신 원하는 종목코드 입력 가능
fin_type = '1'   # 손익계산서
freq_type = '0'  # 연간

df_fin = get_finstate_naver(code, fin_type, freq_type)
if df_fin is not None:
    print(df_fin.loc['2025'])
else:
    print("재무 데이터 없음")
