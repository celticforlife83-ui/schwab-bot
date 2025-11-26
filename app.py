from flask import Flask, request, jsonify
from indicators import calculate_indicators

# Create the web app object
app = Flask(__name__)

# 1) Home page – simple check
@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"

# 2) Health check – used by Render
@app.route("/healthz")
def healthz():
    return "OK"

# 3) Status endpoint – tiny control panel
@app.route("/status")
def status():
    data = {
        "bot": "schwab-bot",
        "version": "0.2.0",
        "mode": "signal_only",        # later: 'live_trading'
        "schwab_connected": False,    # later: True when OAuth works
    }
    return jsonify(data)

# 4) Schwab auth start – placeholder
@app.route("/schwab/auth/start")
def schwab_auth_start():
    """
    Later:
      - Redirect to Schwab login (OAuth)
    Now:
      - Just a placeholder route.
    """
    return "Schwab auth start – not wired yet."

# 5) Schwab auth callback – placeholder
@app.route("/schwab/auth/callback")
def schwab_auth_callback():
    """
    Later:
      - Receive code/token from Schwab
      - Exchange for access + refresh token
    Now:
      - Just a placeholder route.
    """
    return "Schwab auth callback – not wired yet."

# 6) NEW: Indicator test endpoint
@app.route("/indicator-test", methods=["POST"])
def indicator_test():
    """
    Send one candle + indicators and get back our processed view.
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Expected JSON body"}), 400

    try:
        result = calculate_indicators(payload)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Local dev only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)