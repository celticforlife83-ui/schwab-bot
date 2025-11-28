import pandas as pd
import numpy as np

def compute_indicators(candles):
    """
    candles: list of dicts with:
    timestamp, timeframe, open, high, low, close, volume
    """

    if not candles:
        return None, []

    df = pd.DataFrame(candles).copy()

    # Ensure numeric
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # -----------------------------
    # EMAs
    # -----------------------------
    for span in (5, 10, 20, 50):
        df[f"EMA{span}"] = df["close"].ewm(span=span, adjust=False).mean()

    # -----------------------------
    # MAs
    # -----------------------------
    for window in (5, 9, 20):
        df[f"MA{window}"] = df["close"].rolling(window=window, min_periods=1).mean()

    # -----------------------------
    # Bollinger Bands
    # -----------------------------
    mid = df["close"].rolling(20, min_periods=1).mean()
    std = df["close"].rolling(20, min_periods=1).std(ddof=0)

    df["BOLL_MID"] = mid
    df["BOLL_UPPER"] = mid + 2 * std
    df["BOLL_LOWER"] = mid - 2 * std

    # -----------------------------
    # MACD 12, 26, 9
    # -----------------------------
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()

    df["MACD_LINE"] = ema12 - ema26
    df["MACD_SIGNAL"] = df["MACD_LINE"].ewm(span=9, adjust=False).mean()
    df["MACD_HIST"] = df["MACD_LINE"] - df["MACD_SIGNAL"]

    # -----------------------------
    # RSI 14
    # -----------------------------
    delta = df["close"].diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    avg_gain = gains.rolling(14, min_periods=1).mean()
    avg_loss = losses.rolling(14, min_periods=1).mean()

    RS = avg_gain / (avg_loss + 1e-9)

    df["RSI14"] = 100 - (100 / (1 + RS))

    # -----------------------------
    # ATR 14
    # -----------------------------
    prev_close = df["close"].shift(1)

    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - prev_close).abs()
    tr3 = (df["low"] - prev_close).abs()

    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    df["ATR14"] = true_range.rolling(14, min_periods=1).mean()

    # -----------------------------
    # Williams %R 14
    # -----------------------------
    hh = df["high"].rolling(14, min_periods=1).max()
    ll = df["low"].rolling(14, min_periods=1).min()

    df["WILLR14"] = -100 * ((hh - df["close"]) / (hh - ll + 1e-9))

    # -----------------------------
    # Return format
    # -----------------------------
    latest = df.iloc[-1].to_dict()
    all_rows = df.to_dict(orient="records")

    return latest, all_rows
