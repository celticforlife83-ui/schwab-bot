from flask import Flask, jsonify, request
from collections import defaultdict
from indicators import compute_indicators
from signal_logic import classify_trend
from utils import sanitize_latest_indicators

# -------------------------------------------------
# Create the Flask app
# -------------------------------------------------
app = Flask(__name__)

# -------------------------------------------------
# In-memory candle store (Multi-Timeframe Analysis)
# -------------------------------------------------
CANDLES = defaultdict(lambda: defaultdict(list))
MAX_CANDLES_PER_TIMEFRAME = 300  # Keep a cap for cleanliness

# -------------------------------------------------
# Basic routes (health + status)
# -------------------------------------------------
@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"

@app.route("/healthz")
def healthz():
    return "OK"

@app.route("/status")
def status():
    # Count total stored candles across symbols/timeframes
    total_candles = sum(len(tf_list) for symbol in CANDLES.values() for tf_list in symbol.values())
    data = {
        "bot": "schwab-bot",
        "version": "0.2.0",
        "mode": "signal_only",        # later: 'live_trading'
        "schwab_connected": False,    # later: True when OAuth works
        "stored_candles": total_candles,
    }
    return jsonify(data)

# -------------------------------------------------
# Candle feed endpoint  (this is what ReqBin talks to)
# -------------------------------------------------
@app.route("/feed/candle", methods=["POST"])
def feed_candle():
    """
    Accepts one candle and stores it under CANDLES[symbol][timeframe].

    Example JSON body:
    {
      "symbol": "SPX",               # default "SPX" if missing
      "timestamp": "2025-11-26T10:30:00",
      "timeframe": "1m",
      "open": 6800.5,
      "high": 6810.0,
      "low": 6789.4,
      "close": 6805.7,
      "volume": 420000
    }
    """
    data = request.get_json(force=True) or {}

    symbol = str(data.get("symbol", "SPX"))
    timeframe = str(data.get("timeframe", "1m"))

    required_keys = ["timestamp", "open", "high", "low", "close"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        return jsonify({
            "ok": False,
            "error": f"Missing keys: {missing}"
        }), 400

    candle = {
        "timestamp": str(data["timestamp"]),
        "timeframe": timeframe,  # store provided timeframe string
        "open": float(data["open"]),
        "high": float(data["high"]),
        "low": float(data["low"]),
        "close": float(data["close"]),
        "volume": float(data.get("volume", 0.0)),
    }

    # Append to nested store and trim per timeframe
    CANDLES[symbol][timeframe].append(candle)
    CANDLES[symbol][timeframe] = CANDLES[symbol][timeframe][-MAX_CANDLES_PER_TIMEFRAME:]

    return jsonify({
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "stored_count": len(CANDLES[symbol][timeframe]),
        "last_candle": candle
    })

# -------------------------------------------------
# Analysis endpoint (indicator snapshot)
# -------------------------------------------------
@app.route("/analysis", methods=["GET"])
def analysis():
    """
    Returns indicator snapshot for the latest candle in a timeframe.

    Query params:
      symbol: e.g. "SPX" (defaults to "SPX")
      timeframe: e.g. "1m", "5m", "15m" (defaults to "1m")
    """
    symbol = request.args.get("symbol", "SPX")
    timeframe = request.args.get("timeframe", "1m")

    candles_for_tf = CANDLES.get(symbol, {}).get(timeframe, [])

    if not candles_for_tf:
        return jsonify({
            "ok": False,
            "error": f"No candles stored for symbol '{symbol}' and timeframe '{timeframe}' yet."
        }), 400

    latest, _all_rows = compute_indicators(candles_for_tf)

    if latest is None:
        return jsonify({
            "ok": False,
            "error": "Not enough data to compute indicators."
        }), 400

    clean_latest = sanitize_latest_indicators(latest)

    return jsonify({
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "candle_count": len(candles_for_tf),
        "latest": clean_latest
    })

# -------------------------------------------------
# Signal endpoint (trend classification)
# -------------------------------------------------
@app.route("/signal", methods=["GET"])
def signal():
    """Returns latest indicators and classified trend for the requested symbol/timeframe."""
    symbol = request.args.get("symbol", "SPX")
    timeframe = request.args.get("timeframe", "1m")

    candles_for_tf = CANDLES.get(symbol, {}).get(timeframe, [])
    if not candles_for_tf:
        return jsonify({
            "ok": False,
            "error": f"No candles stored for symbol '{symbol}' and timeframe '{timeframe}' yet."
        }), 400

    latest, _all_rows = compute_indicators(candles_for_tf)
    if latest is None:
        return jsonify({
            "ok": False,
            "error": "Not enough data to compute indicators."
        }), 400

    clean_latest = sanitize_latest_indicators(latest)
    signal_data = classify_trend(clean_latest)

    return jsonify({
        "ok": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "latest": clean_latest,
        "signal": signal_data,
    })

# -------------------------------------------------
# Multi-Timeframe Signal endpoint (MTA)
# -------------------------------------------------
@app.route("/mtf-signal", methods=["GET"])
def mtf_signal():
    """Returns signals across multiple requested timeframes for a given symbol."""
    symbol = request.args.get("symbol", "SPX")
    timeframes_raw = request.args.get("timeframes", "1m,5m,15m")
    timeframes_list = [tf.strip() for tf in timeframes_raw.split(",") if tf.strip()]

    results = {}
    for tf in timeframes_list:
        candles_for_tf = CANDLES.get(symbol, {}).get(tf, [])
        if len(candles_for_tf) >= 1:
            latest, _ = compute_indicators(candles_for_tf)
            results[tf] = {
                "latest": sanitize_latest_indicators(latest),
                "signal": classify_trend(latest)
            }
        else:
            results[tf] = {"error": f"Not enough data for {tf}."}

    return jsonify({"symbol": symbol, "ok": True, "timeframes": results})

# -------------------------------------------------
# Local dev entry point (Render ignores this)
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)