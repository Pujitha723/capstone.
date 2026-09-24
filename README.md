# capstone/ data_pipeline
import sqlite3
from pathlib import path
import requests
from bs4 import Beautifulsoup
import pandas as pd

BASE_URL = "https://books.toscrape.com/"
START_URL = DATA_DIR / "books.db"
FX_RATE_GBP_TO_INR = 105.50

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "books.db"
OUTPUT_PATH = DATA_DIR / "query_outputs.txt"

HEADERS = {
     "User-Agent": "Mozilla/5.0 (Capstone Data Pipeline)"
}

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

def get_soup(url):
     response = requests.get(url, headers=HEADERS,  timeout=20)
     response.raise_for_status()
     return Beautifulsoup(response,text, "html.parser")


def scarpe_books():
    """Scrape the first All Products pages (100 catalogue rows)."""
    rows = []

    for page in range(1,6):
        url = BASE_URL + f"catalogue/page-{page}.html"
