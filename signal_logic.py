def classify_trend(latest_indicators: dict) -> dict:
    """
    Analyzes the latest indicator snapshot to classify the market trend.

    Rules defined for strong trend alignment (Bullish/Bearish):
    1. EMA Stack: EMA5 > EMA10 > EMA20 (Bullish) or EMA5 < EMA10 < EMA20 (Bearish).
    2. Price Position: Close price relative to EMA20.
    3. Momentum Confirmation: MACD and RSI confirmation.

    :param latest_indicators: Dict containing the latest computed indicators.
    :return: Dict with the trend classification and rule verification.
    """
    if not latest_indicators or not latest_indicators.get("close"):
        return {"trend": "ERROR", "reason": ["Not enough data."]}

    # Extract core values
    close = latest_indicators.get("close", 0)
    EMA5 = latest_indicators.get("EMA5", close)
    EMA10 = latest_indicators.get("EMA10", close)
    EMA20 = latest_indicators.get("EMA20", close)
    MACD_LINE = latest_indicators.get("MACD_LINE", 0)
    MACD_SIGNAL = latest_indicators.get("MACD_SIGNAL", 0)
    RSI14 = latest_indicators.get("RSI14", 50)
    BOLL_UPPER = latest_indicators.get("BOLL_UPPER", close * 1.05)
    BOLL_LOWER = latest_indicators.get("BOLL_LOWER", close * 0.95)

    # --- 1. Check for Bullish Trend ---
    is_ema_stacked_bull = EMA5 > EMA10 and EMA10 > EMA20
    is_price_above_ema20 = close > EMA20
    is_momentum_bull = MACD_LINE > MACD_SIGNAL and RSI14 > 50

    if is_ema_stacked_bull and is_price_above_ema20 and is_momentum_bull:
        return {
            "trend": "BULLISH",
            "reason": [
                "Strong EMA stack (5>10>20)",
                "Price above EMA20",
                "MACD crossover & RSI > 50",
            ],
            "strength": "STRONG"
        }

    # --- 2. Check for Bearish Trend ---
    is_ema_stacked_bear = EMA5 < EMA10 and EMA10 < EMA20
    is_price_below_ema20 = close < EMA20
    is_momentum_bear = MACD_LINE < MACD_SIGNAL and RSI14 < 50

    if is_ema_stacked_bear and is_price_below_ema20 and is_momentum_bear:
        return {
            "trend": "BEARISH",
            "reason": [
                "Strong EMA stack (5<10<20)",
                "Price below EMA20",
                "MACD crossover & RSI < 50",
            ],
            "strength": "STRONG"
        }

    # --- 3. Default to Chop / Consolidation (Weak/No Trade) ---
    return {
        "trend": "CHOP",
        "reason": [
            "EMAs are not cleanly stacked",
            "Price is whipsawing around EMA20",
            "Low momentum or conflicting signals"
        ],
        "strength": "WEAK"
    }