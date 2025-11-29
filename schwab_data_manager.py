import requests
import json
import time
import base64
import os
from datetime import datetime

# ==========================================
# 🔐 USER CONFIGURATION (FILL THESE IN)
# ==========================================
APP_KEY = "YOUR_APP_KEY_HERE"          # "App Key" from Schwab Portal
APP_SECRET = "YOUR_APP_SECRET_HERE"    # "Secret" from Schwab Portal
REDIRECT_URL = "https://127.0.0.1"     # Your approved Redirect URL
# ==========================================

# Constants
TOKEN_FILE = "schwab_tokens.json"
BASE_URL = "https://api.schwab-api.eclipse.trade/marketdata/v1"
AUTH_URL = "https://api.schwab-api.eclipse.trade/v1/oauth/token"

def save_tokens(tokens):
    """Saves tokens to a local file."""
    tokens['expires_at'] = time.time() + tokens.get('expires_in', 1800)
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)
    print(f"✅ Tokens saved to {TOKEN_FILE}")

def load_tokens():
    """Loads tokens from file if they exist."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def get_auth_headers(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}

def authenticate():
    """Handles the full OAuth flow: Load -> Refresh -> or New Login."""
    tokens = load_tokens()

    # 1. Try to Refresh existing tokens
    if tokens:
        if time.time() < tokens['expires_at'] - 60:
            # Token is still valid
            return tokens
        
        print("🔄 Token expired. Refreshing...")
        headers = {
            'Authorization': f"Basic {base64.b64encode(f'{APP_KEY}:{APP_SECRET}'.encode()).decode()}",
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': tokens['refresh_token']
        }
        response = requests.post(AUTH_URL, headers=headers, data=data)
        if response.status_code == 200:
            new_tokens = response.json()
            # Schwab refresh endpoint might not return the refresh_token again, so we keep the old one if needed
            if 'refresh_token' not in new_tokens:
                new_tokens['refresh_token'] = tokens['refresh_token']
            save_tokens(new_tokens)
            return new_tokens
        else:
            print(f"❌ Refresh failed: {response.text}")
            print("➡️ You must log in again.")

    # 2. New Login Flow (Manual First Time)
    auth_link = f"https://api.schwab-api.eclipse.trade/v1/oauth/authorize?client_id={APP_KEY}&redirect_uri={REDIRECT_URL}"
    print("\n⚠️ NO VALID TOKENS FOUND. PLEASE LOG IN.")
    print(f"1. Click this link: {auth_link}")
    print("2. Log in and approve access.")
    print("3. When redirected to a blank page, COPY the full URL from the address bar.")
    
    redirected_url = input("Paste the full redirected URL here: ").strip()
    
    # Extract code from URL
    try:
        code = redirected_url.split("code=")[1].split("%40")[0] + "@"  # Handle encoding quirk
    except IndexError:
         # Fallback for different encoding or clean paste
        if "code=" in redirected_url:
            code = redirected_url.split("code=")[1]
            if "&" in code: code = code.split("&")[0]
        else:
            code = redirected_url

    print(f"🔑 Exchanging code for tokens...")
    headers = {
        'Authorization': f"Basic {base64.b64encode(f'{APP_KEY}:{APP_SECRET}'.encode()).decode()}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URL
    }
    
    response = requests.post(AUTH_URL, headers=headers, data=data)
    if response.status_code == 200:
        tokens = response.json()
        save_tokens(tokens)
        return tokens
    else:
        print(f"❌ Login Failed: {response.text}")
        return None

def download_spx_history(tokens):
    """Downloads SPX history using the valid token."""
    print("\n📈 Requesting SPX Data for 2024-10-28...")
    
    # timestamps for Oct 28 2024 (approximate market hours in ms)
    start_ms = 1730122200000 
    end_ms = 1730145600000

    params = {
        "symbol": "$SPX",
        "periodType": "day",
        "period": 1,
        "frequencyType": "minute",
        "frequency": 1,
        "startDate": start_ms,
        "endDate": end_ms,
        "needExtendedHoursData": "true"
    }
    
    response = requests.get(f"{BASE_URL}/pricehistory", headers=get_auth_headers(tokens), params=params)
    
    if response.status_code == 200:
        data = response.json()
        candles = data.get('candles', [])
        print(f"✅ SUCCESS: Downloaded {len(candles)} candles.")
        
        filename = "schwab_spx_history.json"
        with open(filename, 'w') as f:
            json.dump(candles, f, indent=2)
        print(f"💾 Saved to {filename}")
        return candles
    else:
        print(f"❌ Data Download Failed: {response.status_code} - {response.text}")
        return []

if __name__ == "__main__":
    tokens = authenticate()
    if tokens:
        download_spx_history(tokens)
