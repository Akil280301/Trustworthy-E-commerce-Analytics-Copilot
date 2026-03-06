"""
src/load_instacart.py
Loads Instacart CSV files into PostgreSQL database.
"""

import sys
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from tqdm import tqdm
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DB_CONFIG, DB_URL


def get_connection():
    """Create a psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


def load_small_table(csv_path, table_name, engine):
    """Load small dimension tables."""
    print(f"\n📥 Loading {table_name}...")
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
    print(f"   ✅ Loaded {len(df):,} rows into {table_name}")
    return len(df)


def load_large_table_chunked(csv_path, table_name, engine, chunksize=50000):
    """Load large fact tables in chunks."""
    print(f"\n📥 Loading {table_name} (chunked)...")
    
    total_rows = sum(1 for _ in open(csv_path)) - 1
    chunks = pd.read_csv(csv_path, chunksize=chunksize)
    rows_loaded = 0
    
    with tqdm(total=total_rows, desc=f"   {table_name}", unit=" rows") as pbar:
        for chunk in chunks:
            chunk.to_sql(table_name, engine, if_exists='append', index=False, method='multi')
            rows_loaded += len(chunk)
            pbar.update(len(chunk))
    
    print(f"   ✅ Loaded {rows_loaded:,} rows into {table_name}")
    return rows_loaded


def validate_load(conn):
    """Validate data load."""
    print("\n🔍 Validating data load...")
    
    with conn.cursor() as cur:
        tables = ['departments', 'aisles', 'products', 'orders', 
                  'order_products__prior', 'order_products__train']
        
        print("\n   Row counts:")
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"      {table:30s} {count:>12,} rows")


def main():
    """Main execution flow."""
    print("=" * 70)
    print("INSTACART DATA WAREHOUSE LOADER")
    print("=" * 70)
    
    data_dir = Path("data_raw")
    files = {
        'departments': data_dir / 'departments.csv',
        'aisles': data_dir / 'aisles.csv',
        'products': data_dir / 'products.csv',
        'orders': data_dir / 'orders.csv',
        'order_products__prior': data_dir / 'order_products__prior.csv',
        'order_products__train': data_dir / 'order_products__train.csv',
    }
    
    print("\n🔍 Checking for CSV files...")
    missing = []
    for name, path in files.items():
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"   ✅ {name:30s} ({size_mb:>6.1f} MB)")
        else:
            print(f"   ❌ {name:30s} NOT FOUND")
            missing.append(name)
    
    if missing:
        print(f"\n❌ ERROR: Missing files: {', '.join(missing)}")
        sys.exit(1)
    
    engine = create_engine(DB_URL)
    
    print("\n" + "=" * 70)
    print("PHASE 1: Loading Dimension Tables")
    print("=" * 70)
    
    load_small_table(files['departments'], 'departments', engine)
    load_small_table(files['aisles'], 'aisles', engine)
    load_small_table(files['products'], 'products', engine)
    
    print("\n" + "=" * 70)
    print("PHASE 2: Loading Fact Tables")
    print("=" * 70)
    
    load_large_table_chunked(files['orders'], 'orders', engine, chunksize=100000)
    load_large_table_chunked(files['order_products__prior'], 'order_products__prior', engine, chunksize=100000)
    load_large_table_chunked(files['order_products__train'], 'order_products__train', engine, chunksize=100000)
    
    print("\n" + "=" * 70)
    print("PHASE 3: Validation")
    print("=" * 70)
    
    conn = get_connection()
    validate_load(conn)
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ DATA LOAD COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()