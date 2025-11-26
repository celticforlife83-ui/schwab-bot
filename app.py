from flask import Flask, jsonify

# Create the web app object
app = Flask(__name__)

# 1) Home page – just a simple check
@app.route("/")
def home():
    return "Schwab bot is alive 🧠📈"

# 2) Health check – used by Render to see if the app is healthy
@app.route("/healthz")
def healthz():
    return "OK"

# 3) Status endpoint – our tiny 'control panel' for now
@app.route("/status")
def status():
    """
    This will become our dashboard for:
    - mode: 'signal' or 'live'
    - connection status to Schwab
    - last time we pulled data
    For now it's just hard-coded.
    """
    data = {
        "bot": "schwab-bot",
        "version": "0.1.0",
        "mode": "signal_only",        # later: 'live_trading'
        "schwab_connected": False,    # later: True when OAuth works
    }
    return jsonify(data)

# 4) Schwab auth start – placeholder (no real login yet)
@app.route("/schwab/auth/start")
def schwab_auth_start():
    """
    In the future:
    - Redirect user to Schwab's login/consent page (OAuth).
    Right now:
    - Just a placeholder so we have the route built.
    """
    return "Schwab auth start – not wired yet."

# 5) Schwab auth callback – placeholder
@app.route("/schwab/auth/callback")
def schwab_auth_callback():
    """
    In the future:
    - Schwab will send us a code/token back here.
    - We'll exchange it for an access token and refresh token.
    Right now:
    - Just a placeholder.
    """
    return "Schwab auth callback – not wired yet."

# This only runs when we start it directly (not on Render)
if __name__ == "__main__":
    # 0.0.0.0 = listen to all connections
    # port 5000 = common default port
    app.run(host="0.0.0.0", port=5000)