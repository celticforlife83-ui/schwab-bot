from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory candle storage (simple for now)
# Later we can swap this for a database if we want.
RECENT_CANDLES = []   # list of dicts, each dict = one candle


# 1) Home page – simple check
@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"


# 2) Health check – used by Render
@app.route("/healthz")
def healthz():
    return "OK"


# 3) Status – tiny control panel
@app.route("/status")
def status():
    data = {
        "bot": "schwab-bot",
        "version": "0.2.0",
        "mode": "signal_only",          # later: 'live_trading'
        "schwab_connected": False,      # later: True when OAuth works
        "stored_candles": len(RECENT_CANDLES),
    }
    return jsonify(data)


# 4) Schwab auth start – placeholder
@app.route("/schwab/auth/start")
def schwab_auth_start():
    return "Schwab auth start – not wired yet."


# 5) Schwab auth callback – placeholder
@app.route("/schwab/auth/callback")
def schwab_auth_callback():
    return "Schwab auth callback – not wired yet."


# 6) FEED ENDPOINT – this is the important new one
#    This is where we push candles + indicators into the bot.
@app.route("/feed", methods=["POST"])
def feed():
    """
    Expected JSON example:

    {
      "timestamp": "2025-11-18 09:35",
      "symbol": "SPX",
      "timeframe": "1m",
      "open": 6647.95,
      "high": 6654.36,
      "low": 6643.92,
      "close": 6643.92,

      "EMA5": 6647.95,
      "EMA10": 6652.45,
      "EMA20": 6655.88,
      "EMA50": 6656.50,

      "MA5": 6641.66,
      "MA9": 6654.69,
      "MA20": 6660.55,

      "BOLL_mid": 6660.55,
      "BOLL_upper": 6685.45,
      "BOLL_lower": 6635.65,

      "MACD": -2.68,
      "MACD_signal": 0.25,
      "MACD_hist": -2.93,

      "RSI": 42.93,
      "ATR": 10.06,
      "WR": -61.13,
      "TTM": -8.13,
      "AO": -15.41,
      "Volume": 10.20
    }
    """

    payload = request.get_json(silent=True)

    if payload is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    # Minimum fields we absolutely need
    required_fields = ["timestamp", "open", "high", "low", "close"]
    missing = [f for f in required_fields if f not in payload]

    if missing:
        return jsonify({
            "error": "Missing required fields",
            "missing": missing
        }), 400

    # Optional: give defaults for symbol/timeframe
    if "symbol" not in payload:
        payload["symbol"] = "SPX"
    if "timeframe" not in payload:
        payload["timeframe"] = "1m"

    # Store the candle
    RECENT_CANDLES.append(payload)

    # Simple cap so memory doesn’t grow forever
    MAX_CANDLES = 5000
    if len(RECENT_CANDLES) > MAX_CANDLES:
        # remove oldest
        RECENT_CANDLES.pop(0)

    return jsonify({
        "status": "ok",
        "stored_candles": len(RECENT_CANDLES),
        "last_timestamp": payload["timestamp"],
        "symbol": payload["symbol"],
        "timeframe": payload["timeframe"],
    }), 200


# 7) DEBUG: quick peek at last N candles (read-only)
@app.route("/feed/last", methods=["GET"])
def feed_last():
    """
    Small helper to see what the bot has in memory.
    NEVER for production UI, just for us to debug.
    """
    # how many to show (default 5)
    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5

    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    data = RECENT_CANDLES[-limit:]

    return jsonify({
        "count": len(data),
        "candles": data
    })


# This only runs when starting locally with `python app.py`
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)