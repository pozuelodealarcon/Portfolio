
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
import requests
from bs4 import BeautifulSoup, NavigableString
import requests
from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup
import re
import requests
import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_fcf_naver(code):
    url = f"https://finance.naver.com/item/main.nhn?code={code}"
    response = requests.get(url)
    response.encoding = 'euc-kr'
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 재무제표 페이지 URL (현금흐름표)
    cf_url = f"https://finance.naver.com/item/main.nhn?code={code}#tab_cfs"
    cf_response = requests.get(cf_url)
    cf_response.encoding = 'euc-kr'
    cf_soup = BeautifulSoup(cf_response.text, "html.parser")
    
    # 네이버 금융은 동적 로딩(스크립트로 재무제표 로딩)이라 바로 FCF 테이블 못 찾을 수도 있음.
    # 대신 재무제표는 네이버 금융에서 '재무제표 데이터'로 JSON 혹은 API 제공 안함.

    # 그래서 일단은 네이버 증권 '재무제표' 탭을 직접 크롤링하거나,
    # 또는 금융 데이터 전문 API(유료) 사용하는 걸 추천
    
    print("네이버 금융 현금흐름표는 동적 로딩 방식이라 직접 크롤링 어려움.")
    print("대안으로 DART 전자공시 API 또는 증권사 API 사용 권장.")

get_fcf_naver("005930")
