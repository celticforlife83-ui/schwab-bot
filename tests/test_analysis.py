"""Tests for the /analysis endpoint JSON serialization."""
import json


def test_analysis_serialization():
    """
    Test that /analysis returns properly serialized JSON with native Python types.
    
    Verifies:
    1. GET /analysis returns HTTP 200 after feeding candles
    2. Response body is valid JSON parsable by json.loads()
    3. All numeric indicator fields and close are native Python float
    4. Timestamp field is a str
    """
    from app import app, RECENT_CANDLES
    
    # Clear any existing candles
    RECENT_CANDLES.clear()
    
    client = app.test_client()
    
    # 1. Feed a candle
    resp = client.post('/feed/candle', json={
        'timestamp': '2025-01-01T00:00:00Z',
        'timeframe': '1m',
        'open': 100,
        'high': 101,
        'low': 99,
        'close': 100.5,
        'volume': 1200
    })
    assert resp.status_code == 200
    
    # 2. Request analysis
    resp = client.get('/analysis?timeframe=1m')
    assert resp.status_code == 200
    
    # 3. Validate response is valid JSON
    data = json.loads(resp.data)
    assert data.get('ok') is True
    
    # 4. Get the latest dict
    latest = data.get('latest')
    assert latest is not None
    
    # 5. Validate numeric fields are Python floats
    # Based on indicators.py output keys
    numeric_fields = [
        'EMA5', 'EMA9', 'EMA10', 'EMA20', 'EMA50',
        'MA5', 'MA9', 'MA20',
        'BOLL MID', 'BOLL UPPER', 'BOLL LOWER',
        'close'
    ]
    for field in numeric_fields:
        if field in latest and latest[field] is not None:
            assert isinstance(latest[field], float), \
                f"Field '{field}' should be float, got {type(latest[field]).__name__}"
    
    # 6. Validate timestamp is a string
    assert isinstance(latest.get('timestamp'), str), \
        f"timestamp should be str, got {type(latest.get('timestamp')).__name__}"


def test_analysis_no_candles():
    """Test that /analysis returns 400 when no candles are stored."""
    from app import app, RECENT_CANDLES
    
    # Clear any existing candles
    RECENT_CANDLES.clear()
    
    client = app.test_client()
    
    resp = client.get('/analysis?timeframe=1m')
    assert resp.status_code == 400
    
    data = json.loads(resp.data)
    assert data.get('ok') is False
    assert 'No candles stored' in data.get('error', '')
