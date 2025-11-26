from flask import Flask, jsonify, request

# Global in-memory candle store (if not already defined)
RECENT_CANDLES = []
MAX_CANDLES = 300  # keep last ~300 candles per timeframe for now

@app.route("/feed/candle", methods=["POST"])
def feed_candle():
    """
    Accepts one candle and stores it in RECENT_CANDLES.
    Body example (JSON):
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
