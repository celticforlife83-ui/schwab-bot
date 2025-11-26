import statistics
from typing import List, Dict, Optional

def _safe_float_list(values) -> List[float]:
    """Convert a list-like into a list of floats."""
    return [float(v) for v in values]

def ema(values: List[float], period: int) -> Optional[float]:
    """
    Simple EMA calculator.
    If there are fewer points than the period, we just use the average so far.
    """
    if not values:
        return None

    # If not enough history, use simple average of what we have
    if len(values) < period:
        return sum(values) / len(values)

    k = 2 / (period + 1)  # EMA smoothing factor
    ema_val = values[0]
    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)
    return ema_val

def sma(values: List[float], period: int) -> Optional[float]:
    """
    Simple moving average (MA).
    Uses the last `period` closes, or all if we have fewer.
    """
    if not values:
        return None

    if len(values) < period:
        window = values
    else:
        window = values[-period:]

    return sum(window) / len(window)

def bollinger(values: List[float], period: int = 20, num_std: float = 2.0):
    """
    Bollinger Bands:
    - MID  = SMA(period)
    - UPPER = MID + num_std * stddev
    - LOWER = MID - num_std * stddev
    """
    if not values:
        return None, None, None

    window = values[-period:] if len(values) >= period else values

    if len(window) == 1:
        mid = window[0]
        return mid, mid, mid

    mid = statistics.mean(window)
    std = statistics.pstdev(window)  # population std dev

    upper = mid + num_std * std
    lower = mid - num_std * std
    return mid, upper, lower

def compute_indicators(closes_raw) -> Dict[str, Optional[float]]:
    """
    Main helper for the bot.
    INPUT:
      closes_raw = list of prices (oldest → newest)

    OUTPUT:
      Dict with ALL the fields you care about.
    """
    closes = _safe_float_list(closes_raw)

    ema5 = ema(closes, 5)
    ema9 = ema(closes, 9)
    ema10 = ema(closes, 10)
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)

    ma5 = sma(closes, 5)
    ma9 = sma(closes, 9)
    ma20 = sma(closes, 20)

    boll_mid, boll_upper, boll_lower = bollinger(closes, period=20, num_std=2.0)

    # Keys match the naming style you’ve been using
    return {
        "EMA5": ema5,
        "EMA9": ema9,
        "EMA10": ema10,
        "EMA20": ema20,
        "EMA50": ema50,
        "MA5": ma5,
        "MA9": ma9,
        "MA20": ma20,
        "BOLL MID": boll_mid,
        "BOLL UPPER": boll_upper,
        "BOLL LOWER": boll_lower,
    }