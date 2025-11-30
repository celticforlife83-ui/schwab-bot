import pandas as pd
from pathlib import Path

# Base folder of the project (schwab-bot)
BASE_DIR = Path(__file__).parent

# data/ folder that already has daily/ weekly/ monthly/
DATA_DIR = BASE_DIR / "data"


def _load_csv(subfolder: str, filename: str) -> pd.DataFrame:
    """
    Small helper:
    - subfolder: "daily", "weekly", or "monthly"
    - filename: like "SPY_daily.csv"
    """
    path = DATA_DIR / subfolder / filename
    df = pd.read_csv(path)

    # Try to parse a date column if it exists
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    return df


def load_daily(symbol: str = "SPY") -> pd.DataFrame:
    """Load daily candles from data/daily/<SYMBOL>_daily.csv"""
    return _load_csv("daily", f"{symbol}_daily.csv")


def load_weekly(symbol: str = "SPY") -> pd.DataFrame:
    """Load weekly candles from data/weekly/<SYMBOL>_weekly.csv"""
    return _load_csv("weekly", f"{symbol}_weekly.csv")


def load_monthly(symbol: str = "SPY") -> pd.DataFrame:
    """Load monthly candles from data/monthly/<SYMBOL>_monthly.csv"""
    return _load_csv("monthly", f"{symbol}_monthly.csv")