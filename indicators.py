import pandas as pd
import numpy as np

# === PHASE 2 HELPERS & INDICATORS ===

def compute_sma(values, period):
    """
    Simple moving average of the last 'period' values.
    """
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def compute_ao(candles):
    """
    Awesome Oscillator (AO):
    AO = SMA(5) of median price - SMA(34) of median price
    median price = (high + low) / 2
    """
    if len(candles) < 34:
        return None

    median_prices = [(c['high'] + c['low']) / 2 for c in candles]

    sma5 = compute_sma(median_prices, 5)
    sma34 = compute_sma(median_prices, 34)

    if sma5 is None or sma34 is None:
        return None

    return sma5 - sma34


def compute_momentum(candles, period=10):
    """
    Momentum (MOM) = close_now - close_n_periods_ago
    """
    if len(candles) < period + 1:
        return None

    close_now = candles[-1]['close']
    close_past = candles[-1 - period]['close']
    return close_now - close_past


def compute_ttm_squeeze(candles, ema20, atr14, boll_mid, boll_upper, boll_lower):
    """
    Simplified TTM Squeeze:

    - Build Keltner Channels using EMA20 and ATR14 * 1.5
    - SQUEEZE_ON = Bollinger Bands inside Keltner
    - SQUEEZE_MOM = close_now - SMA20(close)
    """
    if ema20 is None or atr14 is None or boll_mid is None or boll_upper is None or boll_lower is None:
        return {
            'KC_UPPER': None,
            'KC_LOWER': None,
            'SQUEEZE_ON': None,
            'SQUEEZE_MOM': None,
        }

    kc_upper = ema20 + atr14 * 1.5
    kc_lower = ema20 - atr14 * 1.5

    # BB inside KC => squeeze ON
    squeeze_on = (boll_upper < kc_upper) and (boll_lower > kc_lower)

    closes = [c['close'] for c in candles]
    sma20 = compute_sma(closes, 20)
    if sma20 is None:
        squeeze_mom = None
    else:
        squeeze_mom = closes[-1] - sma20

    return {
        'KC_UPPER': kc_upper,
        'KC_LOWER': kc_lower,
        'SQUEEZE_ON': squeeze_on,
        'SQUEEZE_MOM': squeeze_mom,
    }


def compute_distance_from_ema(close, ema):
    """
    Returns (absolute distance, distance as percentage of price).
    """
    if close is None or ema is None:
        return None, None
    dist = close - ema
    dist_pct = dist / close if close != 0 else None
    return dist, dist_pct


def compute_ema_slope(ema_series, lookback=5):
    """
    ema_series: list of EMA values (same length as candles)
    slope = EMA_now - EMA_lookback
    """
    if len(ema_series) < lookback + 1:
        return None
    ema_now = ema_series[-1]
    ema_past = ema_series[-1 - lookback]
    if ema_now is None or ema_past is None:
        return None
    return ema_now - ema_past


def compute_indicators(candles):
    """
    candles: list of dicts with:
    timestamp, timeframe, open, high, low, close, volume, symbol (symbol optional for older data)
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
    # Return format base
    # -----------------------------
    latest = df.iloc[-1].to_dict()
    all_rows = df.to_dict(orient="records")

    # ---- PHASE 2 ADDITIONS ----
    close = latest.get('close')
    ema20 = latest.get('EMA20')
    ema50 = latest.get('EMA50')
    atr14 = latest.get('ATR14')
    boll_mid = latest.get('BOLL_MID')
    boll_upper = latest.get('BOLL_UPPER')
    boll_lower = latest.get('BOLL_LOWER')

    # AO
    latest['AO'] = compute_ao(candles)

    # Momentum (MOM10)
    latest['MOM10'] = compute_momentum(candles, period=10)

    # TTM Squeeze
    ttm = compute_ttm_squeeze(
        candles,
        ema20=ema20,
        atr14=atr14,
        boll_mid=boll_mid,
        boll_upper=boll_upper,
        boll_lower=boll_lower,
    )
    latest['KC_UPPER'] = ttm['KC_UPPER']
    latest['KC_LOWER'] = ttm['KC_LOWER']
    latest['SQUEEZE_ON'] = ttm['SQUEEZE_ON']
    latest['SQUEEZE_MOM'] = ttm['SQUEEZE_MOM']

    # Distance from EMA20 / EMA50
    dist_20, dist_20_pct = compute_distance_from_ema(close, ema20)
    dist_50, dist_50_pct = compute_distance_from_ema(close, ema50)

    latest['DIST_EMA20'] = dist_20
    latest['DIST_EMA20_PCT'] = dist_20_pct
    latest['DIST_EMA50'] = dist_50
    latest['DIST_EMA50_PCT'] = dist_50_pct

    # Optional EMA slopes (commented placeholder)
    # latest['SLOPE_EMA20'] = compute_ema_slope(ema20_series, lookback=5)
    # latest['SLOPE_EMA50'] = compute_ema_slope(ema50_series, lookback=5)

    return latest, all_rows