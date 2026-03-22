# Annotated SQL Examples — Complex Query Patterns

## Pattern 1: Time-Series Analysis
Question: How do orders trend by day of week and hour combined?
```sql
SELECT
  order_dow,
  CASE order_dow WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' ELSE 'Saturday' END AS day_name,
  order_hour_of_day AS hour,
  COUNT(*) AS order_count
FROM orders
GROUP BY order_dow, order_hour_of_day
ORDER BY order_dow, order_hour_of_day;
```

## Pattern 2: Customer Segmentation
Question: Segment customers by order frequency into low, medium, high value.
```sql
WITH user_order_counts AS (
  SELECT user_id, COUNT(*) AS total_orders
  FROM orders
  GROUP BY user_id
)
SELECT
  CASE
    WHEN total_orders <= 3  THEN 'Low (1-3 orders)'
    WHEN total_orders <= 10 THEN 'Medium (4-10 orders)'
    ELSE 'High (10+ orders)'
  END AS segment,
  COUNT(*) AS user_count,
  ROUND(AVG(total_orders), 2) AS avg_orders
FROM user_order_counts
GROUP BY segment
ORDER BY avg_orders;
```

## Pattern 3: Product Affinity / Co-Purchase
Question: Which products are most often bought together with Bananas?
```sql
WITH banana_orders AS (
  SELECT op.order_id
  FROM order_products__prior op
  JOIN products p ON op.product_id = p.product_id
  WHERE p.product_name ILIKE '%banana%'
),
co_purchased AS (
  SELECT p.product_name, COUNT(*) AS co_purchase_count
  FROM order_products__prior op
  JOIN banana_orders bo ON op.order_id = bo.order_id
  JOIN products p ON op.product_id = p.product_id
  WHERE p.product_name NOT ILIKE '%banana%'
  GROUP BY p.product_name
)
SELECT product_name, co_purchase_count
FROM co_purchased
ORDER BY co_purchase_count DESC
LIMIT 10;
```

## Pattern 4: Reorder Behavior by Department
Question: Which departments have the highest reorder rates?
```sql
SELECT
  d.department,
  COUNT(*) AS total_items,
  SUM(op.reordered) AS reordered_items,
  ROUND(100.0 * SUM(op.reordered) / COUNT(*), 2) AS reorder_rate_pct
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY reorder_rate_pct DESC;
```

## Pattern 5: New vs Returning Customer Orders
Question: What percentage of orders each day come from first-time buyers?
```sql
WITH first_orders AS (
  SELECT user_id, MIN(order_number) AS first_order_num
  FROM orders GROUP BY user_id
)
SELECT
  CASE order_dow WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday'
    WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday'
    WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' ELSE 'Saturday' END AS day,
  COUNT(*) AS total_orders,
  SUM(CASE WHEN o.order_number = 1 THEN 1 ELSE 0 END) AS new_customer_orders,
  ROUND(100.0 * SUM(CASE WHEN o.order_number = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS new_pct
FROM orders o
GROUP BY order_dow
ORDER BY order_dow;
```

## Pattern 6: Nutrition Analysis
Question: What are the healthiest most-ordered products?
```sql
SELECT
  p.product_name,
  COUNT(*) AS times_ordered,
  pe.nutrition_grade_fr,
  pe.energy_100g,
  pe.proteins_100g,
  pe.sugars_100g
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN product_enriched pe ON LOWER(p.product_name) = LOWER(pe.product_name)
WHERE pe.nutrition_grade_fr IN ('a', 'b')
GROUP BY p.product_name, pe.nutrition_grade_fr, pe.energy_100g,
         pe.proteins_100g, pe.sugars_100g
ORDER BY times_ordered DESC
LIMIT 10;
```

## Pattern 7: Holiday Impact
Question: Do orders spike around major holidays?
```sql
SELECT
  h.holiday,
  h.date,
  COUNT(o.order_id) AS holiday_orders,
  ROUND(AVG(COUNT(o.order_id)) OVER (), 2) AS avg_daily_orders
FROM orders o
JOIN holiday_features h
  ON EXTRACT(DOY FROM h.date::date) = o.order_id % 365
GROUP BY h.holiday, h.date
ORDER BY holiday_orders DESC;
```

## Pattern 8: Basket Composition
Question: How does average basket size vary by department focus?
```sql
SELECT
  d.department,
  ROUND(AVG(basket.items), 2) AS avg_basket_size
FROM (
  SELECT op.order_id, p.department_id, COUNT(*) AS items
  FROM order_products__prior op
  JOIN products p ON op.product_id = p.product_id
  GROUP BY op.order_id, p.department_id
) basket
JOIN departments d ON basket.department_id = d.department_id
GROUP BY d.department
ORDER BY avg_basket_size DESC;
```

## Pattern 9: User Lifetime Value Proxy
Question: Who are the top 10 most active users by total items ordered?
```sql
SELECT
  o.user_id,
  COUNT(DISTINCT o.order_id) AS total_orders,
  SUM(basket_size.items) AS total_items,
  ROUND(AVG(basket_size.items), 2) AS avg_basket_size,
  MAX(o.order_number) AS max_order_sequence
FROM orders o
JOIN (
  SELECT order_id, COUNT(*) AS items
  FROM order_products__prior
  GROUP BY order_id
) basket_size ON o.order_id = basket_size.order_id
GROUP BY o.user_id
ORDER BY total_items DESC
LIMIT 10;
```

## Pattern 10: Aisle Affinity by Time of Day
Question: Which aisles are most popular in the morning vs evening?
```sql
SELECT
  a.aisle,
  SUM(CASE WHEN o.order_hour_of_day BETWEEN 6 AND 11 THEN 1 ELSE 0 END) AS morning_orders,
  SUM(CASE WHEN o.order_hour_of_day BETWEEN 17 AND 21 THEN 1 ELSE 0 END) AS evening_orders
FROM order_products__prior op
JOIN orders o ON op.order_id = o.order_id
JOIN products p ON op.product_id = p.product_id
JOIN aisles a ON p.aisle_id = a.aisle_id
GROUP BY a.aisle
HAVING SUM(CASE WHEN o.order_hour_of_day BETWEEN 6 AND 11 THEN 1 ELSE 0 END) > 10000
ORDER BY morning_orders DESC
LIMIT 15;
```