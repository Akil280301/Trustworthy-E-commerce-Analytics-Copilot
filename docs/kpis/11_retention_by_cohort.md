# KPI: Retention by Cohort (Advanced)

## Definition
User retention analysis by synthetic cohorts grouped by user_id deciles.

## Business Context
Cohort analysis tracks user retention over their lifecycle. Identifies at what point users churn.

## Tables Used
- `orders`

## Assumptions
- "Cohort" = users grouped into 10 equal buckets by user_id
- "Retained" = has 5+ orders
- Uses order_number as proxy for lifecycle stage

## Limitations
- No actual dates, so cohorts are synthetic
- Cannot measure time-based retention (30-day, 90-day, etc.)

## Gold SQL
```sql
WITH user_cohorts AS (
    SELECT 
        user_id,
        MIN(order_number) AS first_order,
        MAX(order_number) AS last_order,
        NTILE(10) OVER (ORDER BY user_id) AS cohort
    FROM orders
    GROUP BY user_id
)
SELECT 
    cohort,
    COUNT(DISTINCT user_id) AS total_users,
    COUNT(DISTINCT CASE WHEN last_order >= 5 THEN user_id END) AS retained_after_5,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN last_order >= 5 THEN user_id END) 
                / COUNT(DISTINCT user_id), 2) AS retention_rate_pct
FROM user_cohorts
GROUP BY cohort
ORDER BY cohort;
```

## Expected Result
Retention rates vary by cohort, typically 80-95%.

## Sample Output
```
 cohort | total_users | retained_after_5 | retention_rate_pct 
--------+-------------+------------------+--------------------
      1 |       20647 |            19234 |              93.16
      2 |       20647 |            19145 |              92.73
     ...
```