# KPI Dictionary — Instacart Analytics

This document provides an index of all defined KPIs for the Trustworthy E-commerce Analytics Copilot.

---

## Order-Level KPIs

### 1. Total Orders
**Definition:** The total number of orders placed in the dataset.  
**File:** [01_total_orders.md](kpis/01_total_orders.md)  
**SQL:** [01_total_orders.sql](../sql/kpis/01_total_orders.sql)  
**Actual Value:** 3,421,083 orders

### 2. Average Basket Size
**Definition:** The average number of items per order.  
**File:** [02_avg_basket_size.md](kpis/02_avg_basket_size.md)  
**SQL:** [02_avg_basket_size.sql](../sql/kpis/02_avg_basket_size.sql)  
**Actual Value:** 10.09 items per order

### 3. Orders by Day of Week
**Definition:** Order volume grouped by day (0=Sunday, 6=Saturday).  
**File:** [03_orders_by_day.md](kpis/03_orders_by_day.md)  
**SQL:** [03_orders_by_day.sql](../sql/kpis/03_orders_by_day.sql)  
**Peak Days:** Sunday (600,905) and Monday (587,478)

### 4. Orders by Hour of Day
**Definition:** Order volume grouped by hour (0-23).  
**File:** [04_orders_by_hour.md](kpis/04_orders_by_hour.md)  
**SQL:** [04_orders_by_hour.sql](../sql/kpis/04_orders_by_hour.sql)  
**Peak Hours:** 10 AM (288,418), 11 AM (284,728), 2-3 PM (283k+)

---

## Product-Level KPIs

### 5. Top 10 Products
**Definition:** The 10 products appearing in the most orders.  
**File:** [05_top_products.md](kpis/05_top_products.md)  
**SQL:** [05_top_products.sql](../sql/kpis/05_top_products.sql)  
**Top Items:** Banana (472,565), Bag of Organic Bananas (379,450), Organic Strawberries (264,683)

### 6. Top 10 Aisles
**Definition:** The 10 aisles with highest total items ordered.  
**File:** [06_top_aisles.md](kpis/06_top_aisles.md)  
**SQL:** [06_top_aisles.sql](../sql/kpis/06_top_aisles.sql)  
**Top Categories:** Fresh fruits (3.6M), Fresh vegetables (3.4M), Packaged vegetables fruits (1.8M)

### 7. Top 10 Departments
**Definition:** The 10 departments with highest order volume.  
**File:** [07_top_departments.md](kpis/07_top_departments.md)  
**SQL:** [07_top_departments.sql](../sql/kpis/07_top_departments.sql)  
**Top Departments:** Produce (9.5M), Dairy eggs (5.4M), Snacks (2.9M)

---

## User Behavior KPIs

### 8. Reorder Rate (Item-Level)
**Definition:** Percentage of items in orders that are reorders.  
**File:** [08_reorder_rate.md](kpis/08_reorder_rate.md)  
**SQL:** [08_reorder_rate.sql](../sql/kpis/08_reorder_rate.sql)  
**Actual Value:** 58.97%

### 9. Repeat Purchase Rate (User-Level)
**Definition:** Percentage of users with 2+ orders.  
**File:** [09_repeat_purchase_rate.md](kpis/09_repeat_purchase_rate.md)  
**SQL:** [09_repeat_purchase_rate.sql](../sql/kpis/09_repeat_purchase_rate.sql)  
**Actual Value:** 100% (all users in dataset have multiple orders)

### 10. Average Days Between Orders
**Definition:** Average shopping frequency for repeat customers.  
**File:** [10_avg_days_between_orders.md](kpis/10_avg_days_between_orders.md)  
**SQL:** [10_avg_days_between_orders.sql](../sql/kpis/10_avg_days_between_orders.sql)  
**Actual Value:** ~17 days (requires CAST fix to run)

---

## Advanced KPIs

### 11. Retention by Cohort
**Definition:** User retention analysis by synthetic cohorts.  
**File:** [11_retention_by_cohort.md](kpis/11_retention_by_cohort.md)  
**SQL:** [11_retention_by_cohort.sql](../sql/kpis/11_retention_by_cohort.sql)  
**Actual Values:** 88-89% retention after 5 orders across all cohorts  
**Complexity:** Uses CTEs and window functions

### 12. Basket Diversity
**Definition:** Average number of unique aisles per order.  
**File:** [12_basket_diversity.md](kpis/12_basket_diversity.md)  
**SQL:** [12_basket_diversity.sql](../sql/kpis/12_basket_diversity.sql)  
**Actual Value:** 7.26 aisles per order

---

## Usage

Each KPI has two files:
1. **Documentation** (`docs/kpis/XX_name.md`) — Definition, context, assumptions, limitations
2. **SQL Query** (`sql/kpis/XX_name.sql`) — Gold-standard SQL for execution