
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

def get_dcf(ticker):
    url = f"https://financialmodelingprep.com/api/v3/discounted-cash-flow/{ticker}?apikey={FMP_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        if not data:
            print(f"No DCF data found for {ticker}")
            return None
        
        dcf_data = data[0]  # API returns a list
        print(f"Symbol: {dcf_data['symbol']}")
        print(f"DCF Value: {dcf_data['dcf']}")
        print(f"Stock Price: {dcf_data['Stock Price']}")
        return dcf_data

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# Example usage
if __name__ == "__main__":
    ticker = "AAPL"  # You can change this
    get_dcf(ticker)
