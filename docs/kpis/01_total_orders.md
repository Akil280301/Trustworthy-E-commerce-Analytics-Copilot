# KPI: Total Orders

## Definition
The total number of orders placed in the dataset.

## Business Context
Represents overall transaction volume. Used as a baseline metric for calculating rates and percentages.

## Tables Used
- `orders`

## Assumptions
- Counts all orders regardless of `eval_set` (prior, train, test)
- Each `order_id` represents one transaction

## Limitations
- No date range filtering available (dataset has no timestamps)
- Includes incomplete orders if any exist

## Gold SQL
```sql
SELECT COUNT(*) AS total_orders
FROM orders;
```

## Expected Result
Approximately 3.4 million orders.

## Sample Output
```
 total_orders 
--------------
      3421083
```