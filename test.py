
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
import os

# Set your API key (use .env in production)
FMP_API_KEY ='60ZVxqQtumzWp4LVs4PmJOjiNSnbGThu'
import requests
from bs4 import BeautifulSoup

url = 'https://finance.naver.com/item/coinfo.naver?code=012450&target=finsum_more'
resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')

# '재무분석' 섹션의 테이블 tbody에서 TR 태그 중 ROA가 포함된 행 찾기
tbody = soup.select_one('table.schtab > tbody')
for tr in tbody.find_all('tr'):
    cols = [td.get_text(strip=True) for td in tr.find_all('td')]
    if cols and 'ROA' in cols[0]:
        # 보통 컬럼 순서: index 1~n년도의 값들
        roa_values = cols[1:]
        print("ROA (%) values by year:", roa_values)
