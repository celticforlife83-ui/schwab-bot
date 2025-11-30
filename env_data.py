import os
import pandas as pd

# Base folder where we saved the CSVs
BASE_PATH = os.path.join(os.path.dirname(__file__), "data")


def _load_csv(subfolder: str, symbol_name: str, label: str) -> pd.DataFrame:
    """
    Helper to load a CSV like:
    data/<subfolder>/<symbol_name>_<label>.csv
    Example: data/daily/SPX_daily.csv
    """
    path = os.path.join(BASE_PATH, subfolder, f"{symbol_name}_{label}.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_daily(symbol_name: str = "SPX") -> pd.DataFrame:
    return _load_csv("daily", symbol_name, "daily")


def load_weekly(symbol_name: str = "SPX") -> pd.DataFrame:
    return _load_csv("weekly", symbol_name, "weekly")


def load_monthly(symbol_name: str = "SPX") -> pd.DataFrame:
    return _load_csv("monthly", symbol_name, "monthly")