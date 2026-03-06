-- KPI: Top 10 Departments by Order Volume
-- Departments with highest total item count

SELECT 
    d.department,
    COUNT(*) AS items_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY items_ordered DESC
LIMIT 10;