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

# === PHASE 2: Multi-timeframe scoring + day mode ===

def score_timeframe(snapshot):
    """
    Score a single timeframe using trend_label + momentum indicators.
    """
    trend = snapshot.get('trend_label')
    rsi = snapshot.get('RSI14')
    ao = snapshot.get('AO')
    mom = snapshot.get('MOM10')
    macd_hist = snapshot.get('MACD_HIST')
    close = snapshot.get('close')
    ema20 = snapshot.get('EMA20')

    score = 0

    # Trend label base
    if trend == 'BULLISH':
        score += 1
    elif trend == 'BEARISH':
        score -= 1

    # Price vs EMA20
    if close is not None and ema20 is not None:
        if close > ema20:
            score += 1
        elif close < ema20:
            score -= 1

    # RSI strength / weakness
    if rsi is not None:
        if rsi >= 65:
            score += 2      # strong bull
        elif 55 <= rsi < 65:
            score += 1      # mild bull
        elif 35 <= rsi <= 45:
            score += 0      # chop
        elif 30 <= rsi < 35:
            score -= 1      # mild bear
        elif rsi < 30:
            score -= 2      # strong bear

    # MACD histogram
    if macd_hist is not None:
        if macd_hist > 0:
            score += 1
        elif macd_hist < 0:
            score -= 1

    # AO + MOM confirmation
    bull_confirm = (ao is not None and ao > 0) and (mom is not None and mom > 0)
    bear_confirm = (ao is not None and ao < 0) and (mom is not None and mom < 0)

    if bull_confirm:
        score += 1
    elif bear_confirm:
        score -= 1

    # Clamp to [-3, 3]
    if score > 3:
        score = 3
    if score < -3:
        score = -3

    return score


def classify_day_mode(mtf_snapshots):
    """
    Classify overall day: KILL / SCALP_ONLY / NO_TRADE
    mtf_snapshots: { timeframe: snapshot_with_trend_label_or_None }
    """
    scores = {}
    for tf, snap in mtf_snapshots.items():
        if snap:
            scores[tf] = score_timeframe(snap)

    if not scores:
        return {'day_mode': None, 'reason': 'Not enough data to classify day.'}

    def get_snap(tf):
        return mtf_snapshots.get(tf) or {}

    daily = get_snap('day')
    close_daily = daily.get('close')
    atr14_daily = daily.get('ATR14')
    boll_upper = daily.get('BOLL_UPPER')
    boll_lower = daily.get('BOLL_LOWER')
    squeeze_on_daily = daily.get('SQUEEZE_ON')
    squeeze_mom_daily = daily.get('SQUEEZE_MOM')
    ao_daily = daily.get('AO')
    mom_daily = daily.get('MOM10')
    macd_hist_daily = daily.get('MACD_HIST')

    max_score = max(scores.values())
    min_score = min(scores.values())

    # NO_TRADE conditions
    # 1) Strong conflict between bull and bear timeframes
    if max_score >= 2 and min_score <= -2:
        return {
            'day_mode': 'NO_TRADE',
            'reason': 'Strong conflict between timeframes (bull vs bear).'
        }

    # 2) Low volatility + tight daily Bollinger Bands
    if close_daily and atr14_daily and boll_upper and boll_lower:
        atr_ratio = atr14_daily / close_daily
        boll_spread = (boll_upper - boll_lower) / close_daily
        if atr_ratio < 0.004 and boll_spread < 0.01:
            return {
                'day_mode': 'NO_TRADE',
                'reason': 'Low ATR and tight Bollinger Bands (chop).'
            }

    # Potential KILL day logic
    day_score = scores.get('day', 0)
    h1_score = scores.get('1h', 0)
    m30_score = scores.get('30m', 0)

    if close_daily and atr14_daily:
        atr_ratio = atr14_daily / close_daily

        squeeze_fired_long = (squeeze_on_daily is False) and (squeeze_mom_daily is not None and squeeze_mom_daily > 0)
        squeeze_fired_short = (squeeze_on_daily is False) and (squeeze_mom_daily is not None and squeeze_mom_daily < 0)

        bull_mom_ok = (
            ao_daily is not None and ao_daily > 0 and
            mom_daily is not None and mom_daily > 0 and
            macd_hist_daily is not None and macd_hist_daily > 0
        )
        bear_mom_ok = (
            ao_daily is not None and ao_daily < 0 and
            mom_daily is not None and mom_daily < 0 and
            macd_hist_daily is not None and macd_hist_daily < 0
        )

        # Long KILL day
        if day_score >= 2 and h1_score >= 2 and m30_score >= 1 and atr_ratio >= 0.007:
            if (squeeze_fired_long or bull_mom_ok) and min_score > -1:
                return {
                    'day_mode': 'KILL',
                    'reason': 'Bullish alignment (day/1h/30m) with volatility and momentum.'
                }

        # Short KILL day
        if day_score <= -2 and h1_score <= -2 and m30_score <= -1 and atr_ratio >= 0.007:
            if (squeeze_fired_short or bear_mom_ok) and max_score < 1:
                return {
                    'day_mode': 'KILL',
                    'reason': 'Bearish alignment (day/1h/30m) with volatility and momentum.'
                }

    # Default
    return {
        'day_mode': 'SCALP_ONLY',
        'reason': 'Directional edge present but not fully aligned for high conviction.'
    }