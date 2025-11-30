from env_data import load_daily, load_weekly, load_monthly


def main():
    # Load SPY data from the CSVs we already downloaded
    daily = load_daily("SPY")
    weekly = load_weekly("SPY")
    monthly = load_monthly("SPY")

    print("✅ Loaded data from CSV files!\n")

    print(f"Daily rows:   {len(daily)}")
    print(f"Weekly rows:  {len(weekly)}")
    print(f"Monthly rows: {len(monthly)}\n")

    print("First 5 daily candles:")
    print(daily.head())

    print("\nFirst 5 weekly candles:")
    print(weekly.head())

    print("\nFirst 5 monthly candles:")
    print(monthly.head())


if __name__ == "__main__":
    main()