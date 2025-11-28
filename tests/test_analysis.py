"""Tests for the /analysis route JSON serialization."""
from app import app, RECENT_CANDLES
import json


def test_analysis_serialization():
    """Test that /analysis correctly serializes NumPy/Pandas types to native Python types."""
    # Clear any previous state
    RECENT_CANDLES.clear()
    
    client = app.test_client()
    base_price = 100.0
    
    # Feed multiple candles to allow indicators to compute
    for i in range(30):
        ts = f"2025-11-26T10:30:{i:02d}"
        body = {
            "timestamp": ts,
            "timeframe": "1m",
            "open": base_price + i * 0.1,
            "high": base_price + i * 0.1 + 0.5,
            "low": base_price + i * 0.1 - 0.5,
            "close": base_price + i * 0.1 + 0.25,
            "volume": 1000 + i
        }
        resp = client.post('/feed/candle', json=body)
        assert resp.status_code == 200
    
    # Perform GET /analysis
    resp = client.get('/analysis?timeframe=1m')
    assert resp.status_code == 200
    
    # Parse JSON - this should not throw TypeError
    payload = json.loads(resp.data)
    
    # Assert top-level keys present
    assert 'ok' in payload
    assert 'timeframe' in payload
    assert 'candle_count' in payload
    assert 'latest' in payload
    
    assert payload['ok'] is True
    
    latest = payload['latest']
    
    # Assert timestamp is str
    assert isinstance(latest['timestamp'], str)
    
    # For each numeric indicator key + 'close', if value is not None, assert isinstance(value, float)
    numeric_keys = ["close", "EMA5", "EMA10", "EMA20", "EMA50", "MA5", "MA9", "MA20",
                    "BOLL_MID", "BOLL_UPPER", "BOLL_LOWER"]
    for key in numeric_keys:
        val = latest.get(key)
        if val is not None:
            assert isinstance(val, float), f"{key} should be float, got {type(val)}"
