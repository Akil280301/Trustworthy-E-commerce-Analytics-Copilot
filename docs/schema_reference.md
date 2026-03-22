# Schema Reference — Instacart Data Warehouse

## Table: orders
Stores one row per order placed by a user.
- order_id (PK): unique order identifier
- user_id: customer identifier, join to order history
- eval_set: 'prior' or 'train' — use both for full history
- order_number: sequence of orders per user (1 = first ever)
- order_dow: day of week (0=Sunday, 1=Monday ... 6=Saturday)
- order_hour_of_day: hour 0-23
- days_since_prior_order: NULL for first order, else integer days

## Table: order_products__prior
All historical order-product associations (32M rows).
- order_id (FK → orders)
- product_id (FK → products)
- add_to_cart_order: sequence item was added to cart
- reordered: 1 if user bought this product before, 0 if first time

## Table: order_products__train
Same structure as order_products__prior but for train split (1.3M rows).
Use UNION ALL with order_products__prior for complete product history.

## Table: products
Product dimension table.
- product_id (PK)
- product_name
- aisle_id (FK → aisles)
- department_id (FK → departments)

## Table: aisles
- aisle_id (PK)
- aisle: name e.g. 'fresh fruits', 'yogurt', 'chips pretzels'

## Table: departments
- department_id (PK)
- department: name e.g. 'produce', 'dairy eggs', 'snacks'

## Table: product_enriched
Open Food Facts nutrition data joined to Instacart products.
- product_name: matches products.product_name (fuzzy joined)
- categories_en, main_category_en
- energy_100g, fat_100g, saturated_fat_100g
- carbohydrates_100g, sugars_100g, fiber_100g
- proteins_100g, salt_100g, sodium_100g
- nutrition_grade_fr: a/b/c/d/e (a = healthiest)
- ingredients_text, labels_en

## Table: holiday_features
US federal holidays 2004-2021.
- date: holiday date
- holiday: holiday name e.g. 'Christmas Day'
- weekday, month, day, year

## Common JOIN Patterns

### Orders with products (full history):
SELECT o.*, p.product_name, a.aisle, d.department
FROM orders o
JOIN order_products__prior op ON o.order_id = op.order_id
JOIN products p ON op.product_id = p.product_id
JOIN aisles a ON p.aisle_id = a.aisle_id
JOIN departments d ON p.department_id = d.department_id

### Combined prior + train product history:
SELECT product_id, COUNT(*) as times_ordered FROM (
  SELECT product_id FROM order_products__prior
  UNION ALL
  SELECT product_id FROM order_products__train
) all_op GROUP BY product_id

### Holiday order analysis:
SELECT h.holiday, COUNT(o.order_id) as orders
FROM orders o
JOIN holiday_features h ON DATE(o.order_id::text::date) = h.date
GROUP BY h.holiday