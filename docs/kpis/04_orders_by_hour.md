# KPI: Orders by Hour of Day

## Definition
The number of orders grouped by hour of day (0-23).

## Business Context
Identifies peak ordering times. Critical for delivery scheduling, system capacity planning, and promotional timing.

## Tables Used
- `orders`

## Assumptions
- `order_hour_of_day`: 0 = midnight, 12 = noon, 23 = 11 PM
- All orders included regardless of eval_set

## Limitations
- No timezone information (assumes single timezone for all users)
- Cannot distinguish between order placement time vs delivery time

## Gold SQL
```sql
SELECT 
    order_hour_of_day AS hour,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_hour_of_day
ORDER BY order_hour_of_day;
```

## Expected Result
Peak hours typically 10 AM - 4 PM. Late night/early morning has lowest volume.

## Sample Output
```
 hour | order_count 
------+-------------
    0 |       38951
    1 |       20292
    2 |       12190
  ...
   10 |      288418
   11 |      284728
   12 |      272841
  ...
   23 |       60253
```