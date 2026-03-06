# KPI: Reorder Rate (Item-Level)

## Definition
The percentage of items in orders that are reorders (user has purchased this product before).

## Business Context
Indicates customer loyalty and product stickiness. High reorder rates suggest strong product-market fit and habitual purchasing.

## Tables Used
- `order_products__prior`

## Assumptions
- `reordered = 1` means the user ordered this product in a previous order
- `reordered = 0` means first time purchasing this product
- Uses only prior orders

## Limitations
- Cannot identify which specific prior order contained the product
- First-time orders have no reorder data (all items are reordered=0)

## Gold SQL
```sql
SELECT 
    ROUND(100.0 * SUM(reordered) / COUNT(*), 2) AS reorder_rate_pct
FROM order_products__prior;
```

## Expected Result
Approximately 58-60% of items are reorders.

## Sample Output
```
 reorder_rate_pct 
------------------
            58.97
```