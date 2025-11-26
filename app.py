from flask import Flask, jsonify, request

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
# Simple analysis stub (we’ll make it smarter later)
# -------------------------------------------------
@app.route("/analysis", methods=["GET", "POST"])
def analysis():
    """
    For now just reports how many candles we have stored.
    Later this will run your real options logic.
    """
    return jsonify({
        "ok": True,
        "message": "Analysis endpoint",
        "stored_candles": len(RECENT_CANDLES),
    })

# -------------------------------------------------
# Local dev entry point (Render ignores this)
# -------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)