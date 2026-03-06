-- KPI: Top 10 Most Ordered Products
-- Products appearing in the most orders

SELECT 
    p.product_name,
    COUNT(DISTINCT op.order_id) AS times_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
GROUP BY p.product_name
ORDER BY times_ordered DESC, p.product_name
LIMIT 10;