# Data Sources Documentation

This document describes all datasets used in the Trustworthy E-commerce Analytics Copilot project.

---

## 1. Instacart Market Basket Analysis

**Source:** Kaggle Competition  
**URL:** https://www.kaggle.com/competitions/instacart-market-basket-analysis/data  
**License:** Competition data (public use for educational/research)  
**Downloaded:** February 18, 2026

### Description
The Instacart Online Grocery Shopping Dataset contains 3+ million grocery orders from over 200,000 Instacart users. Each order includes products purchased, order sequence, day of week, hour of day, and days since prior order.

### Files & Structure

#### orders.csv (~109 MB, ~3.4M rows)
Contains order-level information.
- `order_id`: Unique order identifier
- `user_id`: Customer identifier
- `eval_set`: train/test/prior split
- `order_number`: Sequence number for user (1st, 2nd, 3rd order, etc.)
- `order_dow`: Day of week (0-6)
- `order_hour_of_day`: Hour of day (0-23)
- `days_since_prior_order`: Days since last order (null for first order)

#### order_products__prior.csv (~578 MB, ~32.4M rows)
Products purchased in prior orders (training data).
- `order_id`: Foreign key to orders
- `product_id`: Foreign key to products
- `add_to_cart_order`: Sequence in which product was added
- `reordered`: 1 if user has ordered this product before, 0 otherwise

#### order_products__train.csv (~25 MB, ~1.4M rows)
Products purchased in train orders (held-out evaluation set).
- Same structure as order_products__prior.csv

#### products.csv (~2.2 MB, ~49,688 rows)
Product catalog.
- `product_id`: Unique product identifier
- `product_name`: Name of product
- `aisle_id`: Foreign key to aisles
- `department_id`: Foreign key to departments

#### aisles.csv (~3 KB, 134 rows)
Product aisle categories.
- `aisle_id`: Unique aisle identifier
- `aisle`: Aisle name (e.g., "yogurt", "fresh vegetables")

#### departments.csv (~270 bytes, 21 rows)
High-level product departments.
- `department_id`: Unique department identifier
- `department`: Department name (e.g., "dairy eggs", "produce")

### Relevance to Project
- **Primary data source** for all analytics queries
- Supports KPI calculation (basket size, reorder rate, user retention, etc.)
- Rich temporal features (day, hour, days since prior order)
- Realistic e-commerce transaction patterns

### Known Limitations
- No pricing/revenue data (all analysis is quantity-based)
- Anonymized user IDs (no demographics)
- Time period not specified (orders are sequenced but not dated)
- Products are identified by ID only (no UPC/barcode)

### Data Quality Notes
- Referential integrity: All product_id, aisle_id, department_id have valid foreign keys
- No null values in critical fields (order_id, product_id)
- `days_since_prior_order` is null for first orders (expected behavior)

---

## 2. Open Food Facts

**Source:** Kaggle Dataset (originally from Open Food Facts database)  
**URL:** https://www.kaggle.com/datasets/openfoodfacts/world-food-facts  
**License:** Open Database License (ODbL)  
**Downloaded:** February 18, 2026

### Description
Open Food Facts is a collaborative, free, and open database of food products from around the world. Contains product metadata including nutrition facts, ingredients, allergens, labels, and packaging.

### Files & Structure

#### en.openfoodfacts.org.products.tsv (~1 GB, ~1M+ rows)
Tab-separated file with 150+ columns including:
- `product_name`: Product name
- `brands`: Brand name(s)
- `categories`: Product categories (hierarchical, comma-separated)
- `countries`: Countries where sold
- `ingredients_text`: Ingredient list
- `nutrition_grade_fr`: Nutri-Score (A-E)
- `energy_100g`, `fat_100g`, `sugars_100g`, etc.: Nutritional values per 100g
- `additives_tags`, `allergens_tags`: Tags for additives and allergens

### Relevance to Project
- **Product enrichment** for Instacart products (Module 5)
- Enables nutrition-based analytics (e.g., "healthy basket" analysis)
- Category/brand metadata improves product matching
- Supports advanced features like allergen tracking, organic product identification

### Known Limitations
- **Data quality varies** — crowd-sourced, not all fields populated
- **Product matching challenge** — Instacart product names must be fuzzy-matched to OFFF products
- Global database — need to filter to US/English products
- Many null values in nutritional fields

### Data Quality Notes
- Estimated match rate to Instacart: 30-50% (will validate in Module 5)
- Plan: Use product name + category fuzzy matching with manual validation sample

---

## 3. US Holiday Dates (2004-2021)

**Source:** Kaggle Dataset  
**URL:** https://www.kaggle.com/datasets/donnetew/us-holiday-dates-2004-2021  
**License:** Public domain  
**Downloaded:** February 18, 2026

### Description
List of US federal holidays and observances from 2004-2021.

### Files & Structure

#### US Holiday Dates (2004-2021).csv (~16 KB, ~180 rows)
- `Date`: Holiday date (YYYY-MM-DD)
- `Holiday`: Holiday name (e.g., "New Year's Day", "Thanksgiving")

### Relevance to Project
- **Temporal feature engineering** (Module 6)
- Enables holiday impact analysis on order patterns
- Supports seasonality detection in KPIs

### Known Limitations
- Limited time range (2004-2021) — Instacart data period unknown, may not align
- Federal holidays only (no regional/state holidays)
- No distinction between observed vs. actual date (e.g., if holiday falls on weekend)

### Data Quality Notes
- Clean, structured data with no nulls
- Will create derived features: `is_holiday`, `days_to_next_holiday`, `holiday_week`

---

## PII & Privacy Statement

**All datasets are publicly available and contain no Personally Identifiable Information (PII).**

- Instacart: User IDs are anonymized integers with no demographic or contact information
- Open Food Facts: Product data only, no user information
- US Holidays: Public calendar data

No special privacy handling required.

---

## Next Steps (Module 2)

1. Load Instacart CSVs into PostgreSQL
2. Create schema with proper foreign keys and indexes
3. Validate row counts and referential integrity
4. Document any data cleaning decisions
