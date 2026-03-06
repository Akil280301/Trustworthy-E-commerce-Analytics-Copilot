-- KPI: Average Days Between Orders
-- Average shopping frequency for repeat customers

SELECT 
    ROUND(CAST(AVG(days_since_prior_order) AS NUMERIC), 2) AS avg_days_between_orders
FROM orders
WHERE days_since_prior_order IS NOT NULL;