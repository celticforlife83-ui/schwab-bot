import pandas as pd
import os


def load_env_data():
    """
    Load Alpha Vantage CSV data from predefined file paths.
    
    Reads daily, weekly, and monthly SPY data from the data/ directory
    and returns them as pandas DataFrames in a dictionary.
    
    Returns:
        dict: A dictionary containing DataFrames for each timeframe:
              {"daily": daily_df, "weekly": weekly_df, "monthly": monthly_df}
    
    Raises:
        FileNotFoundError: If any of the required CSV files are missing.
    """
    # Define the expected file paths for each timeframe
    file_paths = {
        "daily": "data/daily/SPY_daily.csv",
        "weekly": "data/weekly/SPY_weekly.csv",
        "monthly": "data/monthly/SPY_monthly.csv",
    }
    
    # Check that all required files exist before attempting to load
    missing_files = []
    for timeframe, path in file_paths.items():
        if not os.path.exists(path):
            missing_files.append(path)
    
    # Raise a clear error if any files are missing
    if missing_files:
        raise FileNotFoundError(
            f"Missing required CSV files: {', '.join(missing_files)}. "
            "Please ensure all Alpha Vantage data files are present."
        )
    
    # Load each CSV file into a pandas DataFrame
    env_data = {}
    for timeframe, path in file_paths.items():
        # Read the CSV file with the date column as the index
        df = pd.read_csv(path, index_col="date", parse_dates=True)
        env_data[timeframe] = df
    
    return env_data


def _get_column_value(row, standard_name, alpha_vantage_name):
    """
    Helper to get column value supporting both standard and Alpha Vantage naming.
    
    Args:
        row: pandas Series representing a row of data
        standard_name: Standard column name (e.g., "open")
        alpha_vantage_name: Alpha Vantage column name (e.g., "1. open")
    
    Returns:
        The value from the row using whichever column name exists.
    """
    if standard_name in row:
        return row.get(standard_name)
    return row.get(alpha_vantage_name)


def get_latest_env_snapshot(env_data):
    """
    Extract the most recent data row from each timeframe DataFrame.
    
    Accepts the output dictionary from load_env_data() and extracts
    the latest row for daily, weekly, and monthly timeframes.
    
    Args:
        env_data: Dictionary with keys "daily", "weekly", "monthly",
                  each containing a pandas DataFrame with date index.
    
    Returns:
        dict: A dictionary with the latest snapshot for each timeframe:
              {
                "daily": {"date": ..., "open": ..., "high": ..., "low": ..., "close": ..., "volume": ...},
                "weekly": {...},
                "monthly": {...}
              }
              The "date" field is converted to an ISO format string.
    """
    # Column name mapping: standard name -> Alpha Vantage name
    column_mapping = {
        "open": "1. open",
        "high": "2. high",
        "low": "3. low",
        "close": "4. close",
        "volume": "5. volume",
    }
    
    snapshot = {}
    
    # Process each timeframe to extract the most recent row
    for timeframe in ["daily", "weekly", "monthly"]:
        df = env_data[timeframe]
        
        # Get the most recent row (last row after sorting by date index)
        # Ensure the DataFrame is sorted by date in ascending order
        df_sorted = df.sort_index()
        latest_row = df_sorted.iloc[-1]
        
        # Get the date from the index (which is the date)
        latest_date = df_sorted.index[-1]
        
        # Build the snapshot dictionary for this timeframe
        # Convert date to ISO format string for JSON compatibility
        row_dict = {"date": latest_date.isoformat()}
        
        # Extract each column value using the helper function
        for standard_name, av_name in column_mapping.items():
            row_dict[standard_name] = _get_column_value(latest_row, standard_name, av_name)
        
        snapshot[timeframe] = row_dict
    
    return snapshot
