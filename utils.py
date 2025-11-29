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
    return out;


def sanitize_snapshot(latest_candle, indicators):
    """
    Build a rich snapshot using both the latest candle and its indicators.
    Used for multi-timeframe analysis (/mtf-signal and day_mode).
    """
    if latest_candle is None or indicators is None:
        return {}

    return {
        # Core candle info
        'timestamp': latest_candle.get('timestamp'),
        'timeframe': latest_candle.get('timeframe'),
        'symbol': latest_candle.get('symbol'),
        'open': latest_candle.get('open'),
        'high': latest_candle.get('high'),
        'low': latest_candle.get('low'),
        'close': latest_candle.get('close'),
        'volume': latest_candle.get('volume'),

        # Existing indicators
        'EMA5': indicators.get('EMA5'),
        'EMA10': indicators.get('EMA10'),
        'EMA20': indicators.get('EMA20'),
        'EMA50': indicators.get('EMA50'),
        'MA5': indicators.get('MA5'),
        'MA9': indicators.get('MA9'),
        'MA20': indicators.get('MA20'),
        'BOLL_MID': indicators.get('BOLL_MID'),
        'BOLL_UPPER': indicators.get('BOLL_UPPER'),
        'BOLL_LOWER': indicators.get('BOLL_LOWER'),
        'MACD_LINE': indicators.get('MACD_LINE'),
        'MACD_SIGNAL': indicators.get('MACD_SIGNAL'),
        'MACD_HIST': indicators.get('MACD_HIST'),
        'RSI14': indicators.get('RSI14'),
        'ATR14': indicators.get('ATR14'),
        'WILLR14': indicators.get('WILLR14'),

        # Phase 2 indicators
        'AO': indicators.get('AO'),
        'MOM10': indicators.get('MOM10'),
        'KC_UPPER': indicators.get('KC_UPPER'),
        'KC_LOWER': indicators.get('KC_LOWER'),
        'SQUEEZE_ON': indicators.get('SQUEEZE_ON'),
        'SQUEEZE_MOM': indicators.get('SQUEEZE_MOM'),
        'DIST_EMA20': indicators.get('DIST_EMA20'),
        'DIST_EMA20_PCT': indicators.get('DIST_EMA20_PCT'),
        'DIST_EMA50': indicators.get('DIST_EMA50'),
        'DIST_EMA50_PCT': indicators.get('DIST_EMA50_PCT'),
        # Future optional slopes
        # 'SLOPE_EMA20': indicators.get('SLOPE_EMA20'),
        # 'SLOPE_EMA50': indicators.get('SLOPE_EMA50'),
    };
