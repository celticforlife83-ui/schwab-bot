import requests
import pandas as pd
import os

# ==========================================
# CONFIG
# ==========================================
API_KEY = "YOUR_ALPHA_VANTAGE_API_KEY"  # TODO: replace with my real Alpha Vantage key
BASE_URL = "https://www.alphavantage.co/query"

# Make sure data folders exist
os.makedirs("data/daily", exist_ok=True)
os.makedirs("data/weekly", exist_ok=True)
os.makedirs("data/monthly", exist_ok=True)

# Map the function name to the JSON key Alpha Vantage uses
TIME_SERIES_KEYS = {
    "TIME_SERIES_DAILY_ADJUSTED": "Time Series (Daily)",
    "TIME_SERIES_DAILY": "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": "Weekly Time Series",
    "TIME_SERIES_WEEKLY_ADJUSTED": "Weekly Adjusted Time Series",
    "TIME_SERIES_MONTHLY": "Monthly Time Series",
}


def get_time_series(function_name: str, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
    """
    Generic downloader for Alpha Vantage time series.

    - function_name: e.g. 'TIME_SERIES_DAILY_ADJUSTED', 'TIME_SERIES_WEEKLY', etc.
    - symbol: e.g. 'SPY'
    - outputsize: 'compact' or 'full' (only used for DAILY / DAILY_ADJUSTED)
    """
    params = {
        "function": function_name,
        "symbol": symbol,
        "apikey": API_KEY,
        "datatype": "json",
    }

    # Only daily endpoints support outputsize
    if "DAILY" in function_name:
        params["outputsize"] = outputsize

    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    ts_key = TIME_SERIES_KEYS.get(function_name)
    if ts_key not in data:
        raise ValueError(
            f"Time series key '{ts_key}' not found in response. "
            f"Response keys: {list(data.keys())}"
        )

    ts = data[ts_key]

    # Convert to DataFrame (index is the date string)
    df = pd.DataFrame.from_dict(ts, orient="index")
    df.index = pd.to_datetime(df.index)  # convert index to datetime
    df = df.sort_index()  # oldest → newest

    # Convert numeric columns to floats
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def fetch_daily(symbol: str = "SPY", adjusted: bool = False, outputsize: str = "compact") -> str:
    """
    Fetch daily or daily-adjusted data and save to data/daily/{symbol}_daily.csv
    Returns the output file path.
    """
    function_name = "TIME_SERIES_DAILY_ADJUSTED" if adjusted else "TIME_SERIES_DAILY"
    df = get_time_series(function_name, symbol, outputsize=outputsize)

    out_file = f"data/daily/{symbol}_daily.csv"
    df.to_csv(out_file, index_label="date")
    print(f"Saved {len(df)} daily rows for {symbol} to {out_file}")
    return out_file


def fetch_weekly(symbol: str = "SPY", adjusted: bool = False) -> str:
    """
    Fetch weekly or weekly-adjusted data and save to data/weekly/{symbol}_weekly.csv
    Returns the output file path.
    """
    function_name = "TIME_SERIES_WEEKLY_ADJUSTED" if adjusted else "TIME_SERIES_WEEKLY"
    df = get_time_series(function_name, symbol)

    out_file = f"data/weekly/{symbol}_weekly.csv"
    df.to_csv(out_file, index_label="date")
    print(f"Saved {len(df)} weekly rows for {symbol} to {out_file}")
    return out_file


def fetch_monthly(symbol: str = "SPY") -> str:
    """
    Fetch monthly data and save to data/monthly/{symbol}_monthly.csv
    Returns the output file path.
    """
    df = get_time_series("TIME_SERIES_MONTHLY", symbol)

    out_file = f"data/monthly/{symbol}_monthly.csv"
    df.to_csv(out_file, index_label="date")
    print(f"Saved {len(df)} monthly rows for {symbol} to {out_file}")
    return out_file


if __name__ == "__main__":
    # Example: fetch environment data for SPY
    fetch_daily("SPY", adjusted=False, outputsize="compact")
    fetch_weekly("SPY", adjusted=False)
    fetch_monthly("SPY")