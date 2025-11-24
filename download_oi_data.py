from flask import Flask, render_template, request, flash, redirect, url_for
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import datetime
import requests
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key45dxvxdfet4423442423'

# === CONFIG ===
DATA_DIR = 'data'
BASE_URL = 'https://nsearchives.nseindia.com/content/nsccl/fao_participant_oi_{}.csv'
os.makedirs(DATA_DIR, exist_ok=True)

# === HOLIDAYS ===
NSE_HOLIDAYS = [
    datetime.date(2025, 2, 26),
    datetime.date(2025, 3, 14),
    datetime.date(2025, 3, 31),
    datetime.date(2025, 4, 10),
    datetime.date(2025, 4, 14),
    datetime.date(2025, 4, 18),
    datetime.date(2025, 5, 1),
    datetime.date(2025, 8, 15),
    datetime.date(2025, 8, 27),
    datetime.date(2025, 10, 2),
    datetime.date(2025, 10, 21),
    datetime.date(2025, 10, 22),
    datetime.date(2025, 11, 5),
    datetime.date(2025, 12, 25),
]

def get_date_string(date):
    return date.strftime('%d%m%Y')

def adjust_to_weekday(date):
    """Adjust date backward if it's Sat/Sun"""
    if date.weekday() == 5:
        return date - datetime.timedelta(days=1)  # Saturday → Friday
    elif date.weekday() == 6:
        return date - datetime.timedelta(days=2)  # Sunday → Friday
    else:
        return date

def adjust_for_holidays(date):
    """
    Keep adjusting backward until the date is not a weekend or NSE holiday.
    """
    while date in NSE_HOLIDAYS or date.weekday() > 4:
        date = date - datetime.timedelta(days=1)
    return date

def download_csv(date):
    date_str = get_date_string(date)
    url = BASE_URL.format(date_str)
    save_path = os.path.join(DATA_DIR, f"{date_str}.csv")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.nseindia.com",
    }

    print(f"Downloading: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"✅ Downloaded: {save_path}")
        return save_path
    else:
        raise Exception(f"❌ Failed to download {url} — Status: {response.status_code}")

date_input = datetime.datetime.strptime('28-07-2025', '%d-%m-%Y')