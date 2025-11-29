import requests
import pandas as pd
from datetime import datetime
import time
import os

# ═════════════════════════════════════════
# EDIT THESE 4 LINES ONLY
# ═════════════════════════════════════════
BOT_URL     = "https://schwab-bot.onrender.com"   # ← YOUR RENDER URL
CSV_FILE    = "SPX_2024-10-28_1m.csv"                # ← your 1-minute CSV for Oct 28
SYMBOL      = "SPX"
CHECK_EVERY = 15                                     # minutes → how often we ask the bot's brain
# ═════════════════════════════════════════

# Timeframes we want the bot to analyze each time we check it
TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "day"]

# Auto-create folder to save logs
os.makedirs("replay_logs", exist_ok=True)
log_file = f"replay_logs/{SYMBOL}_Oct28_replay.txt"

# Load CSV – must have columns:
# timestamp, open, high, low, close, volume
df = pd.read_csv(CSV_FILE)
df["timestamp"] = pd.to_datetime(df["timestamp"])

print(f"Loaded {len(df)} candles → {df.iloc[0]['timestamp']} to {df.iloc[-1]['timestamp']}")
print("Starting replay – feeding candle by candle…\n")

with open(log_file, "w", encoding="utf-8") as log:
    log.write(f"REPLAY OF {SYMBOL} – OCT 28 2024\n")
    log.write("=" * 70 + "\n\n")

    last_check = None

    for idx, row in df.iterrows():

        # Convert timestamp to bot format
        ts = row["timestamp"].strftime("%Y-%m-%dT%H:%M:%S")

        # EXACT structure your bot expects
        payload = {
            "symbol": SYMBOL,
            "timeframe": "1m",
            "timestamp": ts,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": float(row.get("volume", 0)),
        }

        # Feed candle to your bot
        try:
            requests.post(f"{BOT_URL}/feed/candle", json=payload, timeout=10)
        except Exception as e:
            print(f"Feed failed at {ts}: {e}")

        current_time = row["timestamp"]
        current_str = current_time.strftime("%H:%M")

        # Decide when to check bot's brain
        should_check = False

        if last_check is None:
            should_check = True
        elif (current_time - last_check).total_seconds() >= CHECK_EVERY * 60:
            should_check = True

        # Forced checks at key market times
        if current_str in [
            "09:30","09:45","10:00","10:15","10:30",
            "11:00","11:30","12:00","13:00",
            "14:00","15:00","15:45","16:00"
        ]:
            should_check = True

        # When it's time -> ask the bot
        if should_check:
            try:
                params = {
                    "symbol": SYMBOL,
                    "timeframes": ",".join(TIMEFRAMES),
                }
                r = requests.get(f"{BOT_URL}/mtf-signal", params=params, timeout=10)
                data = r.json()
            except Exception as e:
                print(f"MTF call failed at {current_str}: {e}")
                data = None

            if data:
                mode   = data.get("day_mode", "???")
                reason = data.get("day_mode_reason", "")

                line = f"{current_str} → {mode:12} | {reason}"
                print(line)
                log.write(line + "\n")

                # Show trends per timeframe
                tfs = data.get("timeframes", {})
                trend_bits = []
                for tf, snap in tfs.items():
                    if snap is None:
                        trend_bits.append(f"{tf}:None")
                    else:
                        trend_bits.append(f"{tf}:{snap.get('trend_label', '?')}")
                trend_summary = " | ".join(trend_bits)

                log.write(f"    → {trend_summary}\n\n")
            else:
                line = f"{current_str} → NO RESPONSE"
                print(line)
                log.write(line + "\n\n")

            last_check = current_time
            time.sleep(0.1)  # don’t overload Render

    # Final classification at end of day
    print("\n" + "=" * 60)
    print("FINAL CLASSIFICATION FOR THE DAY")

    try:
        params = {
            "symbol": SYMBOL,
            "timeframes": ",".join(TIMEFRAMES),
        }
        final = requests.get(f"{BOT_URL}/mtf-signal", params=params, timeout=10).json()

        final_mode   = final.get("day_mode", "???")
        final_reason = final.get("day_mode_reason", "")
    except Exception as e:
        print(f"Final /mtf-signal failed: {e}")
        final_mode   = "???"
        final_reason = "No final response"

    print(f"END OF DAY → {final_mode} | {final_reason}")

    log.write("\n" + "=" * 60 + "\n")
    log.write(f"FINAL → {final_mode} | {final_reason}\n")

print(f"\nReplay finished! Log saved → {log_file}")
print("Open the txt file and compare to your memory of Oct 28.")