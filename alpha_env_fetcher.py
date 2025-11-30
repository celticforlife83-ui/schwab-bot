import requests
import pandas as pd
import os

API_KEY = "EIPBVQENOWS4IGOW"  # keep your key here
BASE_URL = "https://www.alphavantage.co/query"

# We will treat this as SPX for the bot.
# Alpha Vantage often uses ^GSPC for the S&P 500 index.
SYMBOL = "^GSPC"   # index
OUTPUT_SYMBOL_NAME = "SPX"  # how we label the files for your bot

TIME_SERIES_KEYS = {
    "TIME_SERIES_DAILY": "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": "Weekly Time Series",
    "TIME_SERIES_MONTHLY": "Monthly Time Series",
}

def fetch_series(function_name: str, folder: str, label: str):
    params = {
        "function": function_name,
        "symbol": SYMBOL,
        "apikey": API_KEY,
        "datatype": "json",
    }
    # daily supports outputsize
    if "DAILY" in function_name:
        params["outputsize"] = "compact"

    resp = requests.get(BASE_URL, params=params)
    data = resp.json()

    ts_key = TIME_SERIES_KEYS[function_name]
    if ts_key not in data:
        raise ValueError(f"{ts_key} not in response. Got keys: {list(data.keys())}")

    ts = data[ts_key]
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.index.name = "date"
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    os.makedirs(folder, exist_ok=True)
    out_path = os.path.join(folder, f"{OUTPUT_SYMBOL_NAME}_{label}.csv")
    df.to_csv(out_path)
    print(f"Saved {len(df)} rows to {out_path}")

def main():
    fetch_series("TIME_SERIES_DAILY", "data/daily", "daily")
    fetch_series("TIME_SERIES_WEEKLY", "data/weekly", "weekly")
    fetch_series("TIME_SERIES_MONTHLY", "data/monthly", "monthly")

if __name__ == "__main__":
    main()
    