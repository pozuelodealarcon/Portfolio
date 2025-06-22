
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
    
def get_per_krx(ticker):
    url = f"https://finance.naver.com/item/main.nhn?code={ticker[:6]}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://finance.naver.com/'
    }

    try:
        res = requests.get(url, headers=headers)
    except Exception as e:
        print('Naver error:', e)
        return None

    soup = BeautifulSoup(res.text, 'html.parser')
    data = {'PBR': None, 'IND_PER': None, 'PER': None, 'DPS YoY': None, 'ROE': None, "IND_ROE": None}

    aside = soup.select_one('div.aside_invest_info')
    if aside:
        rows = aside.select('table tr')
        if rows:
            for row in rows:
                text = row.text
                em = row.select_one('td em')
                if em is None:
                    continue
                per_text = em.text.strip()

                if 'PBR' in text:
                    data['PBR'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None

                elif '동일업종 PER' in text:
                    data['IND_PER'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None

                elif 'PER' in text and 'EPS' in text and '추정PER' not in text:
                    data['PER'] = float(per_text.replace(',', '')) if 'N/A' not in per_text else None
    
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
                    if tds is None:
                        continue
                    else:
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
                    if tds is None:
                        break  # No data to process

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

                    if cleaned_values:
                        data['IND_ROE'] = sum(cleaned_values) / len(cleaned_values)

                    break  # Only process the first ROE row


    return data

# 사용 예시
ticker = "443060.KS"
roe_list = get_per_krx(ticker)
print(roe_list)
