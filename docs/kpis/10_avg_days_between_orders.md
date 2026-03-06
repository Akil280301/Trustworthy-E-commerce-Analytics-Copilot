# KPI: Average Days Between Orders

## Definition
The average number of days between consecutive orders for users.

## Business Context
Indicates shopping frequency and purchase cycle. Lower values suggest more frequent shoppers.

## Tables Used
- `orders`

## Assumptions
- Uses `days_since_prior_order` field
- Excludes first orders (NULL values)
- All eval_sets included

## Limitations
- Skewed by outliers (users who disappeared for months)
- NULL for first-time orders

## Gold SQL
```sql
SELECT 
    ROUND(CAST(AVG(days_since_prior_order) AS NUMERIC), 2) AS avg_days_between_orders
FROM orders
WHERE days_since_prior_order IS NOT NULL;
```

## Expected Result
Approximately 15-20 days between orders.

## Sample Output
```
 avg_days_between_orders 
-------------------------
                   17.09
```