-- KPI: Reorder Rate (Item-Level)
-- Percentage of items that are reorders

SELECT 
    ROUND(100.0 * SUM(reordered) / COUNT(*), 2) AS reorder_rate_pct
FROM order_products__prior;