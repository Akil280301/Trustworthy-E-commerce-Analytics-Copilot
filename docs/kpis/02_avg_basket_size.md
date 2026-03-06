# KPI: Average Basket Size

## Definition
The average number of items per order.

## Business Context
Indicates typical shopping cart size. Higher values suggest larger shopping trips. Used to understand purchasing patterns and inventory planning.

## Tables Used
- `order_products__prior`
- `orders` (optional for filtering)

## Assumptions
- Uses only `prior` orders (training data)
- Counts all items including duplicates if ordered multiple times in one order

## Limitations
- No price data, so basket size is measured in item count, not dollar value

## Gold SQL
```sql
SELECT ROUND(AVG(items_per_order), 2) AS avg_basket_size
FROM (
    SELECT order_id, COUNT(*) AS items_per_order
    FROM order_products__prior
    GROUP BY order_id
) AS order_sizes;
```

## Expected Result
Approximately 10-11 items per order.

## Sample Output
```
 avg_basket_size 
-----------------
           10.09
```