import pandas as pd
from pathlib import Path

# Find the "data" folder relative to this file
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"


def load_csv(path: Path) -> pd.DataFrame:
    """
    Load one CSV (daily / weekly / monthly) and clean it a bit.
    - Makes sure the first column is called 'date'
    - Turns 'date' into a real datetime
    - Sorts from oldest -> newest
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    df = pd.read_csv(path)

    # Alpha Vantage usually puts the date in the first column (index)
    first_col = df.columns[0]
    df = df.rename(columns={first_col: "date"})

    # Turn date into datetime and sort
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def load_env_data():
    """
    Load SPY daily, weekly, and monthly CSVs that we already downloaded.

    Expected files:
      - data/daily/SPY_daily.csv
      - data/weekly/SPY_weekly.csv
      - data/monthly/SPY_monthly.csv

    Returns a dict like:
      {
        "daily": <DataFrame>,
        "weekly": <DataFrame>,
        "monthly": <DataFrame>,
      }
    """
    daily_path = DATA_DIR / "daily" / "SPY_daily.csv"
    weekly_path = DATA_DIR / "weekly" / "SPY_weekly.csv"
    monthly_path = DATA_DIR / "monthly" / "SPY_monthly.csv"

    daily = load_csv(daily_path)
    weekly = load_csv(weekly_path)
    monthly = load_csv(monthly_path)

    return {"daily": daily, "weekly": weekly, "monthly": monthly}


def get_latest_env_snapshot(env_data):
    """
    Take the dict from load_env_data() and grab the LAST row
    (most recent candle) for each timeframe.

    Returns something like:
      {
        "daily":   {"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...},
        "weekly":  {...},
        "monthly": {...},
      }
    """
    snapshots = {}

    for tf_name, df in env_data.items():
        if df.empty:
            continue

        last = df.iloc[-1]

        # Alpha Vantage column names usually look like:
        # '1. open', '2. high', '3. low', '4. close', '5. volume'
        # We'll try to find them even if names are a bit different.
        cols = list(df.columns)

        def find_col(word, default=None):
            for c in cols:
                if word in c.lower():
                    return c
            return default

        open_col = find_col("open")
        high_col = find_col("high")
        low_col = find_col("low")
        close_col = find_col("close")
        volume_col = find_col("volume")

        snapshots[tf_name] = {
            "date": last["date"].isoformat(),
            "open": float(last[open_col]) if open_col else None,
            "high": float(last[high_col]) if high_col else None,
            "low": float(last[low_col]) if low_col else None,
            "close": float(last[close_col]) if close_col else None,
            "volume": float(last[volume_col]) if volume_col else None,
        }

    return snapshots


if __name__ == "__main__":
    # Manual test: load the data and print the most recent candle for each TF
    env = load_env_data()
    latest = get_latest_env_snapshot(env)

    print("Latest higher-timeframe snapshot (from SPY data):")
    for tf, row in latest.items():
        print(f"{tf}: {row}")