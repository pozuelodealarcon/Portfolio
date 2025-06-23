
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
    data = {'PBR': None, 'IND_PER': None, 'PER': None, 'DPS YoY': None, 'ROE': None, "IND_ROE": None, "OpInc": None}


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
        first_three = opinc[:3]
        first_three = list(filter(lambda x: x is not None, first_three))

        # Only compare if we have at least 2 values
        if len(first_three) >= 2:
            data['OpInc'] = all(
                earlier <= later for earlier, later in zip(first_three, first_three[1:])
            )
    return data

import yfinance as yf

def get_recent_quarter_roa(ticker):
    stock = yf.Ticker(ticker)
    
    # Try to get ROA from info dict (may or may not exist)
    roa = stock.info.get('returnOnAssetsQuarterly')
    if roa is not None:
        return roa * 100  # convert to percentage
    

# Example:
ticker = 'AAPL'
roa = get_recent_quarter_roa(ticker)
print(f"Recent quarterly ROA for {ticker}: {roa}%")
