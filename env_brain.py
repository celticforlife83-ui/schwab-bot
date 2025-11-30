import os
import pandas as pd

# This file builds the "environment brain" for SPX:
# - reads daily / weekly / monthly CSVs
# - computes EMAs, Bollinger Bands, ATR (daily)
# - returns a simple snapshot the bot can use


# Where the data folder lives (data/daily, data/weekly, data/monthly)
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")


def _load_csv(path: str) -> pd.DataFrame:
    """
    Load a CSV and normalize column names so we always have:
    ['open', 'high', 'low', 'close', 'volume'] with a datetime index.
    """
    df = pd.read_csv(path)

    # If there is a 'date' column, use it as index
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

    # Alpha Vantage style column names:
    # '1. open', '2. high', '3. low', '4. close', '5. volume'
    rename_map = {
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "5. volume": "volume",
    }
    df = df.rename(columns=rename_map)

    # If columns are still not correct, try to fall back to common names
    fallback_rename = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
    }
    df = df.rename(columns=fallback_rename)

    # Keep only what we care about
    needed = ["open", "high", "low", "close", "volume"]
    existing = [c for c in needed if c in df.columns]
    df = df[existing]

    # Make sure index is sorted (oldest -> newest)
    df = df.sort_index()

    return df


def load_env_data(symbol: str = "SPX") -> dict:
    """
    Load daily / weekly / monthly CSVs for a symbol.
    Returns a dict of DataFrames.
    """
    daily_path = os.path.join(DATA_DIR, "daily", f"{symbol}_daily.csv")
    weekly_path = os.path.join(DATA_DIR, "weekly", f"{symbol}_weekly.csv")
    monthly_path = os.path.join(DATA_DIR, "monthly", f"{symbol}_monthly.csv")

    if not os.path.exists(daily_path):
        raise FileNotFoundError(f"Missing file: {daily_path}")
    if not os.path.exists(weekly_path):
        raise FileNotFoundError(f"Missing file: {weekly_path}")
    if not os.path.exists(monthly_path):
        raise FileNotFoundError(f"Missing file: {monthly_path}")

    daily_df = _load_csv(daily_path)
    weekly_df = _load_csv(weekly_path)
    monthly_df = _load_csv(monthly_path)

    return {
        "daily": daily_df,
        "weekly": weekly_df,
        "monthly": monthly_df,
    }


def _compute_ema(series: pd.Series, span: int) -> float:
    return series.ewm(span=span, adjust=False).mean().iloc[-1]


def _compute_bollinger(series: pd.Series, window: int = 20, num_std: float = 2.0):
    """
    Simple Bollinger Bands on closing price.
    Returns (mid, upper, lower) for the LAST bar.
    """
    rolling = series.rolling(window=window)
    mid = rolling.mean().iloc[-1]
    std = rolling.std().iloc[-1]
    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower


def _compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    """
    Basic ATR on daily data.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean().iloc[-1]
    return float(atr)


def compute_env_indicators(df: pd.DataFrame, kind: str) -> dict:
    """
    Compute EMAs, Bollinger, ATR (if daily) and a simple trend for the LAST bar.
    kind: 'daily', 'weekly', 'monthly'
    """
    if df.empty:
        return {}

    close = df["close"]
    high = df["high"]
    low = df["low"]

    last_close = float(close.iloc[-1])

    ema5 = float(_compute_ema(close, 5))
    ema10 = float(_compute_ema(close, 10))
    ema20 = float(_compute_ema(close, 20))
    ema50 = float(_compute_ema(close, 50))

    boll_mid, boll_upper, boll_lower = _compute_bollinger(close, window=20, num_std=2.0)

    # Simple trend classification
    if ema5 > ema10 > ema20 and last_close > ema20:
        trend = "UPTREND"
    elif ema5 < ema10 < ema20 and last_close < ema20:
        trend = "DOWNTREND"
    else:
        trend = "CHOP"

    # ATR only for daily data
    if kind == "daily":
        atr14 = _compute_atr(df, period=14)
    else:
        atr14 = None

    return {
        "trend": trend,
        "close": last_close,
        "ema5": ema5,
        "ema10": ema10,
        "ema20": ema20,
        "ema50": ema50,
        "boll_mid": float(boll_mid),
        "boll_upper": float(boll_upper),
        "boll_lower": float(boll_lower),
        "atr14": atr14,
    }


def get_environment(symbol: str = "SPX") -> dict:
    """
    Main function: returns a JSON-friendly environment snapshot:
    {
      "symbol": "SPX",
      "daily": { ... },
      "weekly": { ... },
      "monthly": { ... }
    }
    """
    dfs = load_env_data(symbol)

    daily_info = compute_env_indicators(dfs["daily"], kind="daily")
    weekly_info = compute_env_indicators(dfs["weekly"], kind="weekly")
    monthly_info = compute_env_indicators(dfs["monthly"], kind="monthly")

    return {
        "symbol": symbol,
        "daily": daily_info,
        "weekly": weekly_info,
        "monthly": monthly_info,
    }