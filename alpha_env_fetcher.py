import requests
import pandas as pd
import os

# ==========================================
#  Alpha Vantage configuration
# ==========================================
API_KEY = "EIPBVQENOWS4IGOW"  # <-- keep YOUR real key here
BASE_URL = "https://www.alphavantage.co/query"

# We will REQUEST SPY from Alpha Vantage,
# but we will SAVE the files as if they are SPX.
SYMBOL = "SPY"              # what Alpha Vantage understands
OUTPUT_SYMBOL_NAME = "SPX"  # how your bot will label the files

# Map Alpha Vantage function -> JSON key in the response
TIME_SERIES_KEYS = {
    "TIME_SERIES_DAILY": "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": "Weekly Time Series",
    "TIME_SERIES_MONTHLY": "Monthly Time Series",
}


def fetch_series(function_name: str, folder: str, label: str) -> None:
    """
    Fetch a time series from Alpha Vantage and save it as a CSV.

    function_name: one of:
        - "TIME_SERIES_DAILY"
        - "TIME_SERIES_WEEKLY"
        - "TIME_SERIES_MONTHLY"
    folder: where to save the CSV (e.g. "data/daily")
    label: part of the output filename (e.g. "daily" -> SPX_daily.csv)
    """
    params = {
        "function": function_name,
        "symbol": SYMBOL,
        "apikey": API_KEY,
        "datatype": "json",
    }

    # Daily endpoints support outputsize (compact = latest 100 rows)
    if "DAILY" in function_name:
        params["outputsize"] = "compact"

    resp = requests.get(BASE_URL, params=params)
    data = resp.json()

    # Helpful error messages for API issues
    if isinstance(data, dict):
        if "Error Message" in data:
            raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")
        if "Note" in data:
            raise RuntimeError(f"Alpha Vantage notice (rate limit?): {data['Note']}")

    ts_key = TIME_SERIES_KEYS[function_name]
    if ts_key not in data:
        raise ValueError(f"{ts_key} not in response. Got keys: {list(data.keys())}")

    ts = data[ts_key]

    # Convert to DataFrame
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.index.name = "date"
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()  # oldest -> newest

    # Convert numeric columns from strings to floats
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Ensure folder exists
    os.makedirs(folder, exist_ok=True)

    # Save as SPX_xxx.csv so your bot “thinks in SPX”
    out_path = os.path.join(folder, f"{OUTPUT_SYMBOL_NAME}_{label}.csv")
    df.to_csv(out_path)

    print(f"Saved {len(df)} rows to {out_path}")


def main() -> None:
    # Daily, weekly, monthly for SPY (saved as SPX_*.csv)
    fetch_series("TIME_SERIES_DAILY", "data/daily", "daily")
    fetch_series("TIME_SERIES_WEEKLY", "data/weekly", "weekly")
    fetch_series("TIME_SERIES_MONTHLY", "data/monthly", "monthly")


if __name__ == "__main__":
    main()