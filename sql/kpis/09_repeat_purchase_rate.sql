-- KPI: Repeat Purchase Rate (User-Level)
-- Percentage of users with 2+ orders

SELECT 
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN order_number >= 2 THEN user_id END) 
                / COUNT(DISTINCT user_id), 2) AS repeat_purchase_rate_pct
FROM orders;