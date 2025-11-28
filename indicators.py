import pandas as pd
from typing import List, Dict, Optional, Tuple


def compute_indicators(candles: List[Dict]) -> Tuple[Optional[Dict], Optional[pd.DataFrame]]:
    """
    Main helper for the bot.
    INPUT:
      candles = list of candle dicts with keys: timestamp, open, high, low, close, volume

    OUTPUT:
      Tuple of (latest_row_dict, all_rows_dataframe)
      Returns (None, None) if not enough data.
    """
    if not candles or len(candles) < 1:
        return None, None

    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)

    # EMAs
    df['EMA5'] = df['close'].ewm(span=5, adjust=False).mean()
    df['EMA10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()

    # SMAs
    df['MA5'] = df['close'].rolling(window=5, min_periods=1).mean()
    df['MA9'] = df['close'].rolling(window=9, min_periods=1).mean()
    df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()

    # Bollinger Bands
    df['BOLL_MID'] = df['close'].rolling(window=20, min_periods=1).mean()
    df['BOLL_STD'] = df['close'].rolling(window=20, min_periods=1).std()
    df['BOLL_UPPER'] = df['BOLL_MID'] + 2 * df['BOLL_STD']
    df['BOLL_LOWER'] = df['BOLL_MID'] - 2 * df['BOLL_STD']

    # Drop helper column
    df = df.drop(columns=['BOLL_STD'])

    # Get latest row as dict
    latest = df.iloc[-1].to_dict()

    return latest, df
