# KPI: Top 10 Most Ordered Products

## Definition
The 10 products that appear in the most orders.

## Business Context
Identifies best-selling items for inventory prioritization, promotional planning, and product placement decisions.

## Tables Used
- `order_products__prior`
- `products`

## Assumptions
- "Most ordered" = highest number of orders containing the product
- Uses prior orders only
- Ties broken alphabetically by product name

## Limitations
- Does not account for quantity per order (treats 1 item same as multiple)
- No revenue data to distinguish by dollar value

## Gold SQL
```sql
SELECT 
    p.product_name,
    COUNT(DISTINCT op.order_id) AS times_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
ORDER BY times_ordered DESC, p.product_name
LIMIT 10;
```

## Expected Result
Bananas, organic bananas, and staple items typically top the list.

## Sample Output
```
         product_name          | times_ordered 
-------------------------------+---------------
 Banana                        |        472565
 Bag of Organic Bananas        |        379450
 Organic Strawberries          |        264683
 Organic Baby Spinach          |        241921
 Organic Hass Avocado          |        213584
 Organic Avocado               |        176815
 Large Lemon                   |        152657
 Strawberries                  |        142951
 Limes                         |        140627
 Organic Whole Milk            |        137905
```