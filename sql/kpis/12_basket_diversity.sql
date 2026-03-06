-- KPI: Basket Diversity (Advanced)
-- Average number of unique aisles per order

SELECT 
    ROUND(AVG(unique_aisles), 2) AS avg_aisles_per_order
FROM (
    SELECT 
        op.order_id,
        COUNT(DISTINCT p.aisle_id) AS unique_aisles
    FROM order_products__prior op
    JOIN products p ON op.product_id = p.product_id
    GROUP BY op.order_id
) AS order_diversity;