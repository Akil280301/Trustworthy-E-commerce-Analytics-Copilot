"""
src/load_food_facts.py
Loads Open Food Facts TSV into the product_enriched table.
Filters to grocery-relevant rows and aligns with Instacart products.
"""

import sys
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DB_URL

COLS = [
    "code", "product_name", "categories_en", "main_category_en",
    "energy_100g", "fat_100g", "saturated-fat_100g", "carbohydrates_100g",
    "sugars_100g", "fiber_100g", "proteins_100g", "salt_100g", "sodium_100g",
    "nutrition_grade_fr", "ingredients_text", "labels_en", "countries_en"
]

def main():
    print("=" * 70)
    print("OPEN FOOD FACTS LOADER")
    print("=" * 70)

    path = Path("data_raw") / "en.openfoodfacts.org.products.tsv"
    if not path.exists():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    print(f"\nReading {path.name} in chunks (this may take a few minutes)...")

    engine = create_engine(DB_URL)
    total = 0
    chunk_num = 0

    for chunk in pd.read_csv(
        path, sep="\t", usecols=lambda c: c in COLS,
        chunksize=10000, on_bad_lines="skip", low_memory=False
    ):
        chunk_num += 1

        # Filter to rows that have a product name and are food items
        chunk = chunk[chunk["product_name"].notna()]
        chunk = chunk[chunk["countries_en"].str.contains("United States", na=False)]

        if chunk.empty:
            continue

        # Clean column names for postgres
        chunk.columns = [c.replace("-", "_") for c in chunk.columns]

        chunk.to_sql("product_enriched", engine, if_exists="append", index=False, method="multi")
        total += len(chunk)

        if chunk_num % 10 == 0:
            print(f"   Processed {chunk_num * 10000:,} source rows → {total:,} kept so far...")

    print(f"\nLoaded {total:,} rows into product_enriched")
    print("=" * 70)
    print("FOOD FACTS LOAD COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()