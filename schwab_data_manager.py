import requests
import json
import time
import base64
import os
from urllib.parse import urlparse, parse_qs

# ==========================================
# 🔐 USER CONFIGURATION (EDIT THESE 3 LINES)
# ==========================================
APP_KEY = "duVi4SZ4do75pldeMLACvutzg7vJBWMmNYsf26mv3kAQoHmO"       # Paste App Key
APP_SECRET = "p3VfFZXLUIxrR5jAKGg3DDh515stoHup8mmSk9MnolxE96gM48P5v2btimatERAD" # Paste Secret
REDIRECT_URL = "https://127.0.0.1/" # Must match dashboard exactly
# ==========================================

# Constants
TOKEN_FILE = "schwab_tokens.json"
BASE_URL = "https://api.schwabapi.com/marketdata/v1"
AUTH_URL = "https://api.schwabapi.com/v1/oauth/token"

def save_tokens(tokens):
    """Saves tokens to a local file with an expiration timestamp."""
    # Schwab tokens usually last 30 mins (1800s). We set safety buffer.
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 1800)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=4)
    print(f"💾 Tokens saved/updated in {TOKEN_FILE}")

def load_tokens():
    """Loads tokens from file if they exist."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Token file was empty or corrupted.")
            return None
    return None

def authenticate():
    """
    Handles the full OAuth flow: 
    1. Load existing tokens.
    2. Refresh them if expired.
    3. If all else fails, prompt user for manual login.
    """
    tokens = load_tokens()

    # --- CASE A: WE HAVE TOKENS, TRY TO REFRESH ---
    if tokens:
        # Check if they are about to expire (less than 60s left)
        if time.time() < tokens.get("expires_at", 0) - 60:
            return tokens
        
        print("🔄 Tokens expired. Attempting refresh...")
        
        headers = {
            "Authorization": "Basic " + base64.b64encode(f"{APP_KEY}:{APP_SECRET}".encode()).decode(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
        }
        
        response = requests.post(AUTH_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            new_tokens = response.json()
            # CRITICAL: Schwab doesn't always send a NEW refresh token. 
            # If they didn't, we must keep the old one.
            if "refresh_token" not in new_tokens:
                new_tokens["refresh_token"] = tokens["refresh_token"]
            
            save_tokens(new_tokens)
            return new_tokens
        else:
            print(f"❌ Refresh failed ({response.status_code}). Reason: {response.text}")
            print("➡️ Falling back to manual login...")

    # --- CASE B: MANUAL LOGIN (First time or Refresh Failed) ---
    print("\n⚠️ MANUAL AUTHENTICATION REQUIRED")
    
    auth_link = (
        f"https://api.schwabapi.com/v1/oauth/authorize"
        f"?client_id={APP_KEY}&redirect_uri={REDIRECT_URL}"
    )
    
    print(f"1. Copy/Paste this URL into your browser:\n{auth_link}\n")
    print("2. Log in, click 'Allow'.")
    print("3. When you see 'This site can’t be reached', COPY the URL from address bar.")
    
    redirected_url = input("\n👇 Paste the full URL here: ").strip()

    # Extract code safely
    try:
        parsed = urlparse(redirected_url)
        query_params = parse_qs(parsed.query)
        code = query_params.get("code", [None])[0]
    except Exception as e:
        print(f"❌ Error parsing URL: {e}")
        return None

    if not code:
        print("❌ Could not find 'code' in the URL. Did you copy the whole thing?")
        return None

    print("🔑 Exchanging code for access tokens...")
    
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{APP_KEY}:{APP_SECRET}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URL,
    }

    response = requests.post(AUTH_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)
        print("✅ SUCCESS! We are authenticated.")
        return tokens
    else:
        print(f"❌ Authentication Failed: {response.status_code}")
        print(response.text)
        return None

def download_spx_history(tokens):
    """Downloads SPX candles for a specific timeframe."""
    if not tokens:
        print("❌ No tokens available. Cannot download.")
        return

    print("\n📈 Requesting SPX Data (Replay: Oct 28, 2024)...")

    # Hardcoded for the requested replay scenario
    start_ms = 1730122200000  # Oct 28 9:30 AM ET
    end_ms = 1730145600000    # Oct 28 4:00 PM ET

    params = {
        "symbol": "$SPX",  # Schwab uses $ for indices usually
        "periodType": "day",
        "period": 1,
        "frequencyType": "minute",
        "frequency": 1,
        "startDate": start_ms,
        "endDate": end_ms,
        "needExtendedHoursData": "true",
    }

    url = f"{BASE_URL}/pricehistory"
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            candles = data.get("candles", [])
            
            if not candles:
                print("⚠️ Request succeeded, but returned 0 candles. (Market closed? Wrong symbol?)")
            else:
                print(f"✅ SUCCESS: Downloaded {len(candles)} candles.")
                
                # Save to file for inspection
                filename = "schwab_spx_history.json"
                with open(filename, "w") as f:
                    json.dump(candles, f, indent=2)
                print(f"📄 Data saved to {filename}")
                
            return candles
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

if __name__ == "__main__":
    # 1. Authenticate (Auto-refresh or Manual)
    valid_tokens = authenticate()
    
    # 2. If we have tokens, run the download test
    if valid_tokens:
        download_spx_history(valid_tokens)
