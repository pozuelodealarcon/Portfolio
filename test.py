
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
import os
import requests
from pykrx import stock
import datetime as dt
import openpyxl
import math
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
import requests
from io import StringIO
from datetime import datetime

# 예시용 날짜 정규화 함수
def get_date_str(col):
    try:
        return datetime.strptime(col.strip(), "%Y/%m").strftime("%Y-%m")
    except:
        return col.strip()

import pandas as pd
import requests
from io import StringIO
import re

def get_finstate_naver(code, fin_type="0", freq_type="Y"):
    """
    code: 종목 코드 (6자리, 예: "005930")
    fin_type: 재무제표 종류 ("0": 주재무제표, "4": IFRS 연결 등)
    freq_type: "Y" 연간, "Q" 분기
    """
    url = (
        "https://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx"
        f"?cmp_cd={code}&fin_typ={fin_type}&freq_typ={freq_type}"
    )
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"  
    }

    
    resp = requests.get(url, headers=headers)
    resp.encoding = resp.apparent_encoding

    html = resp.text
    if "해당 데이터가 존재하지 않습니다" in html:
        return None

    # 불필요한 header 제거
    html = re.sub(r'<th[^>]*>연간</th>', '', html)
    html = re.sub(r"<span class='span-sub'>\([^)]*\)</span>", "", html)
    
    try:
        df = pd.read_html(StringIO(html))[0]
    except ValueError:
        return None

    # 컬럼 첫줄 삭제(멀티컬럼 제거)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(1)

    df = df.iloc[1:]  # 제목행 제외
    df = df.set_index(df.columns[0])
    df.index.name = "account"
    df.columns = df.columns.str.extract(r'(\d{4})')[0]  # '2025/12'→'2025'
    
    dft = df.T
    dft.index = pd.to_datetime(dft.index + "-12-31", errors='coerce')
    dft = dft.dropna(axis=0, how='all')
    
    # 컬럼명 리네임
    dft.rename(columns={
        '유보율': '자본유보율',
        '현금배당성향': '현금배당성향(%)'
    }, inplace=True)

    return dft.astype(float)


df = get_finstate_naver("005930", fin_type="0", freq_type="Y")
print(df.head())
