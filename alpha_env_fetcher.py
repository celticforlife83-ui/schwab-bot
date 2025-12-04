import requests
import pandas as pd
import os
import time

# ==========================================
# 🔧 CONFIGURATION
# ==========================================
# ⚠️ SECURITY: Consider moving this to os.environ.get("ALPHA_VANTAGE_KEY")
API_KEY = "YOUR_REAL_KEY_HERE" 
BASE_URL = "https://www.alphavantage.co/query"

# We request SPY (Equity) but save as SPX (Index) for the bot's logic
SYMBOL = "SPY"
OUTPUT_SYMBOL_NAME = "SPX"

# Map Function -> JSON Key
TIME_SERIES_KEYS = {
    "TIME_SERIES_DAILY": "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": "Weekly Time Series",
    "TIME_SERIES_MONTHLY": "Monthly Time Series",
}

def fetch_series(function_name: str, folder: str, label: str, mode: str = "compact") -> None:
    """
    function_name: API function (e.g., TIME_SERIES_DAILY)
    folder: Output folder
    label: Filename suffix
    mode: 'compact' (100 rows) or 'full' (20 years history)
    """
    print(f"📥 Fetching {label} ({mode})...")
    
    params = {
        "function": function_name,
        "symbol": SYMBOL,
        "apikey": API_KEY,
        "datatype": "json",
    }

    # Only Daily supports 'full' vs 'compact'. Weekly/Monthly are always full.
    if "DAILY" in function_name:
        params["outputsize"] = mode  # 'compact' or 'full'

    try:
        resp = requests.get(BASE_URL, params=params)
        data = resp.json()
    except Exception as e:
        print(f"❌ Network Error: {e}")
        return

    # Error Handling
    if "Error Message" in data:
        print(f"❌ API Error: {data['Error Message']}")
        return
    if "Note" in data:
        print(f"⚠️ API Note (Rate Limit?): {data['Note']}")
        # If we hit a rate limit, wait 60s (Alpha Vantage free tier is 5 calls/min)
        time.sleep(60) 

    ts_key = TIME_SERIES_KEYS.get(function_name)
    if not ts_key or ts_key not in data:
        print(f"❌ Key '{ts_key}' not found. Keys received: {list(data.keys())}")
        return

    # Parse Data
    ts = data[ts_key]
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.index.name = "date"
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()  # Oldest -> Newest

    # Convert strings to floats
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Save
    os.makedirs(folder, exist_ok=True)
    out_path = os.path.join(folder, f"{OUTPUT_SYMBOL_NAME}_{label}.csv")
    df.to_csv(out_path)
    
    print(f"✅ Saved {len(df)} rows to {out_path}")

def main():
    print("--- 🚀 ALPHA VANTAGE FETCHER ---")
    
    # 1. WEEKLY & MONTHLY (Always Full History)
    fetch_series("TIME_SERIES_WEEKLY", "data/weekly", "weekly")
    fetch_series("TIME_SERIES_MONTHLY", "data/monthly", "monthly")

    # 2. DAILY (Ask User)
    print("\nSelect Mode for DAILY data:")
    print("1: Update (Last 100 days - FAST)")
    print("2: Training (Last 20 Years - SLOW, large file)")
    choice = input("Choice (1/2): ").strip()

    if choice == "2":
        fetch_series("TIME_SERIES_DAILY", "data/daily", "daily", mode="full")
    else:
        fetch_series("TIME_SERIES_DAILY", "data/daily", "daily", mode="compact")

if __name__ == "__main__":
    main()
