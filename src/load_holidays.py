"""
src/load_holidays.py
Loads US Holiday Dates (2004-2021) into the holiday_features table.
"""

import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DB_URL

def main():
    print("=" * 70)
    print("US HOLIDAYS LOADER")
    print("=" * 70)

    path = Path("data_raw") / "US Holiday Dates (2004-2021).csv"
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    print(f"\nReading {path.name}...")
    df = pd.read_csv(path)
    print(f"Columns found: {list(df.columns)}")
    print(df.head(3))

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    engine = create_engine(DB_URL)
    df.to_sql("holiday_features", engine, if_exists="append", index=False, method="multi")

    print(f"\nLoaded {len(df):,} rows into holiday_features")
    print("=" * 70)
    print("HOLIDAYS LOAD COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()