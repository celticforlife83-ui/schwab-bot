import pandas as pd

def compute_indicators(candles):
    """
    candles: list[dict] with keys:
      timestamp, timeframe, open, high, low, close, volume

    Returns:
      latest_indicators: dict with close, timestamp, all EMAs/MAs and Bollinger bands
      all_rows: list[dict] with indicators for every candle (for future use)
    """
    if not candles:
        return None, []

    # Build DataFrame from list of candle dicts
    df = pd.DataFrame(candles).copy()

    # Make sure numeric fields are numeric
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- EMAs ---
    for span in (5, 10, 20, 50):
        df[f"EMA{span}"] = df["close"].ewm(span=span, adjust=False).mean()

    # --- Simple moving averages (MAs) ---
    for window in (5, 9, 20):
        df[f"MA{window}"] = df["close"].rolling(window=window, min_periods=1).mean()

    # --- Bollinger Bands (20 period, 2 std) ---
    window = 20
    mid = df["close"].rolling(window=window, min_periods=1).mean()
    std = df["close"].rolling(window=window, min_periods=1).std(ddof=0)

    df["BOLL_MID"] = mid
    df["BOLL_UPPER"] = mid + 2 * std
    df["BOLL_LOWER"] = mid - 2 * std

    # Latest row with all indicators
    latest = df.iloc[-1].to_dict()
    all_rows = df.to_dict(orient="records")
    return latest, all_rows
