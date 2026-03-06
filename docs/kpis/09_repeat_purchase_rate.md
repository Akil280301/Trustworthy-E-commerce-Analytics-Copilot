# KPI: Repeat Purchase Rate (User-Level)

## Definition
The percentage of users who have placed 2 or more orders.

## Business Context
Measures customer retention at the user level. Higher rates indicate successful customer acquisition and retention.

## Tables Used
- `orders`

## Assumptions
- "Repeat customer" = user with order_number >= 2
- Counts all orders (prior + train + test)

## Limitations
- Does not measure frequency (2 orders vs 100 orders treated the same)
- Cannot determine time span between orders without timestamps

## Gold SQL
```sql
SELECT 
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN order_number >= 2 THEN user_id END) 
                / COUNT(DISTINCT user_id), 2) AS repeat_purchase_rate_pct
FROM orders;
```

## Expected Result
Very high (>95%) since dataset includes users' order histories.

## Sample Output
```
 repeat_purchase_rate_pct 
--------------------------
                    99.87
```