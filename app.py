from flask import Flask, jsonify, request
from indicators import compute_indicators

# -------------------------------------------------
# Create the Flask app
# -------------------------------------------------
app = Flask(__name__)

# -------------------------------------------------
# In-memory candle store
# -------------------------------------------------
RECENT_CANDLES = []
MAX_CANDLES = 300  # keep last ~300 candles for now

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
    data = {
        "bot": "schwab-bot",
        "version": "0.1.0",
        "mode": "signal_only",        # later: 'live_trading'
        "schwab_connected": False,    # later: True when OAuth works
        "stored_candles": len(RECENT_CANDLES),
    }
    return jsonify(data)

# -------------------------------------------------
# Schwab OAuth placeholders
# -------------------------------------------------
@app.route("/schwab/auth/start")
def schwab_auth_start():
    return "Schwab auth start – not wired yet."

@app.route("/schwab/auth/callback")
def schwab_auth_callback():
    return "Schwab auth callback – not wired yet."

# -------------------------------------------------
# Candle feed endpoint  (this is what ReqBin talks to)
# -------------------------------------------------
@app.route("/feed/candle", methods=["POST"])
def feed_candle():
    """
    Accepts one candle and stores it in RECENT_CANDLES.

    Example JSON body:
    {
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

    required_keys = ["timestamp", "timeframe", "open", "high", "low", "close"]
    missing = [k for k in required_keys if k not in data]
    if missing:
        return jsonify({
            "ok": False,
            "error": f"Missing keys: {missing}"
        }), 400

    candle = {
        "timestamp": str(data["timestamp"]),
        "timeframe": str(data["timeframe"]),  # e.g. "1m", "5m"
        "open": float(data["open"]),
        "high": float(data["high"]),
        "low": float(data["low"]),
        "close": float(data["close"]),
        "volume": float(data.get("volume", 0.0)),
    }

    RECENT_CANDLES.append(candle)

    # keep only the most recent MAX_CANDLES
    if len(RECENT_CANDLES) > MAX_CANDLES:
        RECENT_CANDLES.pop(0)

    return jsonify({
        "ok": True,
        "stored_count": len(RECENT_CANDLES),
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
      timeframe: e.g. "1m", "5m", "15m" (defaults to "1m")

    Response:
      {
        "ok": true,
        "timeframe": "1m",
        "candle_count": 123,
        "latest": {
          "timestamp": "...",
          "close": 6805.7,
          "EMA5": ...,
          "EMA10": ...,
          "EMA20": ...,
          "EMA50": ...,
          "MA5": ...,
          "MA9": ...,
          "MA20": ...,
          "BOLL_MID": ...,
          "BOLL_UPPER": ...,
          "BOLL_LOWER": ...
        }
      }
    """
    import pandas as pd
    import numpy as np

    # timeframe filter, default 1m
    timeframe = request.args.get("timeframe", "1m")

    # Filter candles already stored in memory
    candles_for_tf = [c for c in RECENT_CANDLES if c.get("timeframe") == timeframe]

    if not candles_for_tf:
        return jsonify({
            "ok": False,
            "error": f"No candles stored for timeframe '{timeframe}' yet."
        }), 400

    latest, _all_rows = compute_indicators(candles_for_tf)

    if latest is None:
        return jsonify({
            "ok": False,
            "error": "Not enough data to compute indicators."
        }), 400

    def clean(val):
        """Convert pandas/numpy types to native Python types for JSON serialization."""
        if pd.isna(val) or val is None:
            return None
        if isinstance(val, (np.integer, int)):
            return int(val)
        if isinstance(val, (np.floating, float)):
            return float(val)
        return str(val)

    out = {
        "timestamp": clean(latest.get("timestamp")),
        "close": clean(latest.get("close")),
        "EMA5": clean(latest.get("EMA5")),
        "EMA10": clean(latest.get("EMA10")),
        "EMA20": clean(latest.get("EMA20")),
        "EMA50": clean(latest.get("EMA50")),
        "MA5": clean(latest.get("MA5")),
        "MA9": clean(latest.get("MA9")),
        "MA20": clean(latest.get("MA20")),
        "BOLL_MID": clean(latest.get("BOLL_MID")),
        "BOLL_UPPER": clean(latest.get("BOLL_UPPER")),
        "BOLL_LOWER": clean(latest.get("BOLL_LOWER")),
    }

    return jsonify({
        "ok": True,
        "timeframe": timeframe,
        "candle_count": len(candles_for_tf),
        "latest": out
    })

# -------------------------------------------------
# Local dev entry point (Render ignores this)
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)