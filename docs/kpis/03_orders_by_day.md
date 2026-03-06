# KPI: Orders by Day of Week

## Definition
The number of orders grouped by day of week (0 = Sunday, 6 = Saturday).

## Business Context
Identifies peak shopping days and helps with staffing, inventory, and delivery scheduling. Useful for understanding weekly shopping patterns.

## Tables Used
- `orders`

## Assumptions
- `order_dow`: 0 = Sunday, 1 = Monday, ..., 6 = Saturday
- All orders included regardless of eval_set

## Limitations
- Cannot determine actual calendar dates (no timestamps)
- Day-of-week patterns may not represent current behavior if data is old

## Gold SQL
```sql
SELECT 
    order_dow,
    CASE order_dow
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_dow
ORDER BY order_dow;
```

## Expected Result
Sunday (0) and Monday (1) typically have highest order volumes.

## Sample Output
```
 order_dow | day_name  | order_count 
-----------+-----------+-------------
         0 | Sunday    |      600905
         1 | Monday    |      587478
         2 | Tuesday   |      467260
         3 | Wednesday |      436972
         4 | Thursday  |      426339
         5 | Friday    |      453368
         6 | Saturday  |      448761
```