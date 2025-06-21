
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
    url = f"https://finance.naver.com/item/main.nhn?code={ticker[:6]}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    data = {}
    PBR = None
    IND_PER = None
    PER = None

    # 동일업종 PER이 들어있는 박스 찾기
    aside = soup.select_one('div.aside_invest_info')
    if aside:
        rows = aside.select('table tr')
        for row in rows:
            if 'PBR' in row.text:
                per_text = row.select_one('td em').text
                if 'N/A' not in per_text:
                    PBR = float(per_text.replace(',', ''))
                    data['PBR'] =  PBR
                else:
                    data['PBR'] =  None


            if '동일업종 PER' in row.text:
                per_text = row.select_one('td em').text
                if 'N/A' not in per_text:
                    IND_PER = float(per_text.replace(',', ''))
                    data['IND_PER'] =  IND_PER
                else:
                    data['IND_PER'] =  None

            if 'PER' in row.text and 'EPS' in row.text and '추정PER' not in row.text:
                per_text = row.select_one('td em').text
                if 'N/A' not in per_text:
                    PER = float(per_text.replace(',', ''))
                    data['PER'] =  PER
                else:
                    data['PER'] =  None

    return data

print(get_per_krx('064760'))