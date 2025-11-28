def sanitize_latest_indicators(latest_snapshot: dict) -> dict:
    """
    Return a sanitized subset of the latest indicator snapshot for JSON output.
    Centralizes the indicator key whitelist so both /analysis and /signal share the same shape.
    """
    if not isinstance(latest_snapshot, dict):
        return {}

    indicator_keys = [
        # core candle
        "timestamp",
        "close",
        # EMAs
        "EMA5", "EMA10", "EMA20", "EMA50",
        # Simple MAs
        "MA5", "MA9", "MA20",
        # Bollinger Bands
        "BOLL_MID", "BOLL_UPPER", "BOLL_LOWER",
        # Momentum & volatility
        "MACD_LINE", "MACD_SIGNAL", "MACD_HIST",
        "RSI14", "ATR14", "WILLR14",
    ]

    out = {}
    for k in indicator_keys:
        if k in latest_snapshot:
            out[k] = latest_snapshot.get(k)
    return out