-- KPI: Retention by Cohort (Advanced)
-- User retention analysis by synthetic cohorts

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