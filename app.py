from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------- BASIC ROUTES ----------

@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"

@app.route("/healthz")
def healthz():
    return "OK"

@app.route("/status")
def status():
    return jsonify({
        "bot": "schwab-bot",
        "version": "0.1.0",
        "mode": "data_collect_only",
        "schwab_connected": False
    })

# ---------- CANDLE INBOX (FULL INDICATOR VERSION) ----------

@app.route("/candle", methods=["POST"])
def candle():
    payload = request.get_json(force=True, silent=True) or {}

    return jsonify({
        "status": "received",
        "summary": {
            "symbol": payload.get("symbol"),
            "timeframe": payload.get("timeframe"),
            "close": payload.get("close"),
            "ema5": payload.get("ema5"),
            "ema10": payload.get("ema10"),
            "ema20": payload.get("ema20"),
            "ma5": payload.get("ma5"),
            "rsi": payload.get("rsi"),
            "wr": payload.get("williams_r")
        },
        "full": payload  # returns EVERYTHING you sent
    })

# ---------- DEMO PAYLOAD (SO YOU CAN TEST IN BROWSER) ----------

@app.route("/candle/demo")
def candle_demo():
    example_payload = {
        "symbol": "SPX",
        "timeframe": "5m",
        "timestamp": "2025-11-18T10:00:00",
        "open": 6613.35,
        "high": 6613.63,
        "low": 6600.87,
        "close": 6601.40,
        "volume": 46480000,

        "ma5": 6608.22,
        "ma9": 6611.10,
        "ma10": 6612.01,
        "ma20": 6625.44,
        "ma50": 6640.55,
        "ma200": 6722.18,

        "ema5": 6621.01,
        "ema9": 6629.90,
        "ema10": 6633.21,
        "ema12": 6635.10,
        "ema20": 6645.44,
        "ema26": 6650.52,
        "ema50": 6680.80,
        "ema200": 6733.91,

        "boll_mid": 6645.35,
        "boll_upper": 6678.14,
        "boll_lower": 6612.57,

        "macd_line": -12.22,
        "macd_signal": -10.14,
        "macd_histogram": -2.08,

        "rsi": 23.03,
        "williams_r": -99.27,
        "momentum": -25.14,

        "ttm_squeeze_on": True,
        "ttm_histogram": -1.4,

        "atr": 28.4,
        "ao": -15.9
    }

    return jsonify(example_payload)

# ---------- AUTH PLACEHOLDERS ----------

@app.route("/schwab/auth/start")
def schwab_auth_start():
    return "Schwab auth start – not wired yet."

@app.route("/schwab/auth/callback")
def schwab_auth_callback():
    return "Schwab auth callback – not wired yet."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)  
