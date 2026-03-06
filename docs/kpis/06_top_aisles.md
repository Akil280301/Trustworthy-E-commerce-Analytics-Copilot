# KPI: Top 10 Most Popular Aisles

## Definition
The 10 aisles from which the most products are ordered.

## Business Context
Indicates which product categories drive the most volume. Useful for store layout optimization and merchandising strategy.

## Tables Used
- `order_products__prior`
- `products`
- `aisles`

## Assumptions
- "Most popular" = highest total item count ordered from that aisle
- Uses prior orders only

## Limitations
- Does not account for unique products (some aisles may have fewer SKUs but higher volume)

## Gold SQL
```sql
SELECT 
    a.aisle,
    COUNT(*) AS items_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN aisles a ON p.aisle_id = a.aisle_id
GROUP BY a.aisle
ORDER BY items_ordered DESC
LIMIT 10;
```

## Expected Result
Fresh fruits and vegetables typically dominate.

## Sample Output
```
           aisle            | items_ordered 
----------------------------+---------------
 fresh vegetables           |       2959285
 fresh fruits               |       2662403
 packaged vegetables fruits |       1241453
 yogurt                     |       1052722
 packaged cheese            |        924383
 water seltzer sparkling    |        895344
 milk                       |        883830
 chips pretzels             |        799015
 soy lactosefree            |        738247
 bread                      |        710090
```