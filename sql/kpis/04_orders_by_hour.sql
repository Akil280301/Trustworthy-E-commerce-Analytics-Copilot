-- KPI: Orders by Hour of Day
-- Order volume by hour (0-23)

SELECT 
    order_hour_of_day AS hour,
    COUNT(*) AS order_count
FROM orders
GROUP BY order_hour_of_day
ORDER BY order_hour_of_day;