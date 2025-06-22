
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
import requests
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

def get_industry_comparison_roe(ticker):
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://finance.naver.com/'
    }

    res = requests.get(url, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')

    # 동일업종 비교 테이블은 div.section.inner_sub > table.class="compare" 내부에 위치
    compare_table = soup.select_one('div.section.trade_compare table')

    if not compare_table:
        print("동일업종 비교 테이블을 찾을 수 없습니다.")
        return None

    roe = None
    ind_roe = None

    rows = compare_table.select('tr')
    for row in rows:
        th = row.find('th')
        if th and 'ROE' in th.text:
            tds = row.find_all('td')
            result = [td.text.strip().replace('%', '') for td in tds]

            # Try to parse company ROE
            try:
                roe = float(result[0]) if result[0] != '' else None
            except ValueError:
                roe = None

            # Process industry ROE values
            raw_industry_values = result[1:]
            cleaned_values = []

            for item in raw_industry_values:
                if item != '':
                    try:
                        cleaned_values.append(float(item))
                    except ValueError:
                        continue  # Skip invalid entries

            if cleaned_values:
                ind_roe = sum(cleaned_values) / len(cleaned_values)
            else:
                ind_roe = None

    return(roe, ind_roe)


    

# 사용 예시
ticker = "012450"
roe_list = get_industry_comparison_roe(ticker)

print(roe_list)

