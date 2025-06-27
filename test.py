
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

intro_message = (
    f"귀하의 투자 참고를 위해 {date_kr} 기준, "
    f"시가총액 상위 {limit}개 상장기업에 대한 최신 퀀트 분석 자료를 전달드립니다.\n\n"
    "각 기업의 종합 점수는 ‘B-Score’ 항목을 참고해 주시기 바라며, "
    "B-Score가 0점 미만인 기업은 자료에서 제외되었습니다.\n\n"
    "본 자료는 워런 버핏의 투자 철학을 기반으로, "
    "기업의 재무 건전성을 수치화하여 평가한 결과입니다.\n"
    "투자 판단 시에는 정성적 요소에 대한 별도의 면밀한 검토도 "
    "함께 병행하시기를 권장드립니다.\n"
)

print(intro_message)