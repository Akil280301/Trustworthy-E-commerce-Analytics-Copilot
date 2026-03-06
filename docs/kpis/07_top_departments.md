# KPI: Top 10 Departments by Order Volume

## Definition
The 10 departments with the highest total item count ordered.

## Business Context
High-level category performance. Guides departmental resource allocation and category management decisions.

## Tables Used
- `order_products__prior`
- `products`
- `departments`

## Assumptions
- "Top departments" = highest total items ordered
- Uses prior orders only

## Limitations
- Departments vary widely in number of products/aisles, making direct comparison difficult

## Gold SQL
```sql
SELECT 
    d.department,
    COUNT(*) AS items_ordered
FROM order_products__prior op
JOIN products p ON op.product_id = p.product_id
JOIN departments d ON p.department_id = d.department_id
GROUP BY d.department
ORDER BY items_ordered DESC
LIMIT 10;
```

## Expected Result
Produce, dairy, and beverages lead.

## Sample Output
```
      department       | items_ordered 
-----------------------+---------------
 produce               |       9713843
 dairy eggs            |       5165711
 snacks                |       2836112
 beverages             |       2593359
 frozen                |       2148433
 pantry                |       2092271
 bakery                |       1573518
 canned goods          |       1477015
 deli                  |       1187134
 dry goods pasta       |       1081513
```