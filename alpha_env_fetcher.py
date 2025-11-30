import requests
import pandas as pd
import os

API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"  # TODO: replace with my real key
BASE_URL = "https://www.alphavantage.co/query"

# Make sure data folders exist
os.makedirs("data/daily", exist_ok=True)
os.makedirs("data/weekly", exist_ok=True)
os.makedirs("data/monthly", exist_ok=True)