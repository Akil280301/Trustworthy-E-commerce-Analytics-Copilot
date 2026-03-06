# KPI: Basket Diversity (Advanced)

## Definition
The average number of unique aisles (product categories) per order.

## Business Context
Measures shopping trip variety. Higher diversity suggests "big shop" trips vs focused purchases.

## Tables Used
- `order_products__prior`
- `products`
- `aisles`

## Assumptions
- Uses aisles as proxy for product categories
- Higher = more diverse shopping trips
- Uses prior orders only

## Limitations
- Aisle count may not perfectly represent true category diversity

## Gold SQL
```sql
SELECT 
    ROUND(AVG(unique_aisles), 2) AS avg_aisles_per_order
FROM (
    SELECT 
        op.order_id,
        COUNT(DISTINCT p.aisle_id) AS unique_aisles
    FROM order_products__prior op
    JOIN products p ON op.product_id = p.product_id
    GROUP BY op.order_id
) AS order_diversity;
```

## Expected Result
Approximately 5-7 unique aisles per order.

## Sample Output
```
 avg_aisles_per_order 
----------------------
                 6.18
```