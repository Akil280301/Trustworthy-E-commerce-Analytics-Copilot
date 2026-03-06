-- ================================================================
-- Instacart Data Warehouse Schema
-- ================================================================

-- Drop tables if they exist (for clean re-runs)
DROP TABLE IF EXISTS order_products__train CASCADE;
DROP TABLE IF EXISTS order_products__prior CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS aisles CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- ================================================================
-- DIMENSION TABLES
-- ================================================================

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department VARCHAR(100) NOT NULL
);

CREATE TABLE aisles (
    aisle_id INTEGER PRIMARY KEY,
    aisle VARCHAR(100) NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    aisle_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    FOREIGN KEY (aisle_id) REFERENCES aisles(aisle_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- ================================================================
-- FACT TABLES
-- ================================================================

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    eval_set VARCHAR(10) NOT NULL,
    order_number INTEGER NOT NULL,
    order_dow INTEGER NOT NULL CHECK (order_dow BETWEEN 0 AND 6),
    order_hour_of_day INTEGER NOT NULL CHECK (order_hour_of_day BETWEEN 0 AND 23),
    days_since_prior_order FLOAT
);

CREATE TABLE order_products__prior (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    add_to_cart_order INTEGER NOT NULL,
    reordered INTEGER NOT NULL CHECK (reordered IN (0, 1)),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE order_products__train (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    add_to_cart_order INTEGER NOT NULL,
    reordered INTEGER NOT NULL CHECK (reordered IN (0, 1)),
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- ================================================================
-- INDEXES
-- ================================================================

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_eval_set ON orders(eval_set);
CREATE INDEX idx_orders_dow ON orders(order_dow);
CREATE INDEX idx_orders_hour ON orders(order_hour_of_day);

CREATE INDEX idx_products_aisle_id ON products(aisle_id);
CREATE INDEX idx_products_dept_id ON products(department_id);
CREATE INDEX idx_products_name ON products(product_name);

CREATE INDEX idx_order_products_prior_product ON order_products__prior(product_id);
CREATE INDEX idx_order_products_train_product ON order_products__train(product_id);

-- ================================================================
-- ANALYTICS VIEWS
-- ================================================================

CREATE VIEW v_order_items AS
SELECT 
    o.order_id,
    o.user_id,
    o.eval_set,
    o.order_number,
    o.order_dow,
    o.order_hour_of_day,
    o.days_since_prior_order,
    op.product_id,
    op.add_to_cart_order,
    op.reordered,
    p.product_name,
    a.aisle,
    d.department
FROM orders o
JOIN order_products__prior op ON o.order_id = op.order_id
JOIN products p ON op.product_id = p.product_id
JOIN aisles a ON p.aisle_id = a.aisle_id
JOIN departments d ON p.department_id = d.department_id;

CREATE VIEW v_user_summary AS
SELECT 
    user_id,
    COUNT(DISTINCT order_id) as total_orders,
    AVG(days_since_prior_order) as avg_days_between_orders,
    MAX(order_number) as max_order_number
FROM orders
WHERE eval_set = 'prior'
GROUP BY user_id;