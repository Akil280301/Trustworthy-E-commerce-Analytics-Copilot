-- KPI: Average Basket Size
-- Average number of items per order

SELECT ROUND(AVG(items_per_order), 2) AS avg_basket_size
FROM (
    SELECT order_id, COUNT(*) AS items_per_order
    FROM order_products__prior
    GROUP BY order_id
) AS order_sizes;