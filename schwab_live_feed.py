"""
schwab_live_feed.py

This file will later be responsible for:
- talking to the Schwab market data API
- turning price quotes into 1-minute candles
- sending those candles into the bot's /feed/candle endpoint.

Right now it is just a simple demo so we can:
- practice running a separate Python file
- see candles flow into the bot
- test /mtf-signal with a fake live feed.
"""

import time
import requests
from datetime import datetime

# Where our bot is running (Flask app)
BOT_URL = "http://127.0.0.1:5000"
SYMBOL = "SPX"

def send_candle_to_bot(ts: str, open_: float, high: float, low: float, close: float, volume: float) -> None:
    """
    Send ONE candle to our existing /feed/candle endpoint.
    This uses the SAME shape as replay_oct28_1m.py.
    """
    payload = {
        "symbol": SYMBOL,
        "timeframe": "1m",
        "timestamp": ts,
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "volume": float(volume),
    }
    try:
        r = requests.post(f"{BOT_URL}/feed/candle", json=payload, timeout=5)
        r.raise_for_status()
        print(f"✅ Sent candle {ts} → status {r.status_code}")
    except Exception as e:
        print(f"❌ Failed to send candle {ts}: {e}")

def run_fake_demo_feed() -> None:
    """
    TEMPORARY:
    - Every 5 seconds, send a fake 1-minute candle into the bot.
    - This is just to test wiring while we wait for Schwab market data.

    LATER:
    - We will replace this with real Schwab API calls.
    """
    price = 5800.0
    volume = 100000.0

    print("Starting fake demo feed. Press Ctrl+C to stop.")
    while True:
        now = datetime.utcnow().replace(second=0, microsecond=0)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S")

        # Tiny random-style movement (no randomness lib, just simple steps)
        open_ = price
        close = price + 1.0
        high = max(open_, close) + 0.5
        low = min(open_, close) - 0.5

        send_candle_to_bot(ts, open_, high, low, close, volume)

        # Update "price" for next candle
        price = close
        time.sleep(5)

if __name__ == "__main__":
    run_fake_demo_feed()