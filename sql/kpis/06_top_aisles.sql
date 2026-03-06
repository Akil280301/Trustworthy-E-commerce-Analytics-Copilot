-- KPI: Top 10 Most Popular Aisles
-- Aisles with highest total item count ordered

SELECT 
    a.aisle,
    COUNT(*) AS items_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN aisles a ON p.aisle_id = a.aisle_id
GROUP BY a.aisle
ORDER BY items_ordered DESC
LIMIT 10;