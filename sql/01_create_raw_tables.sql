-- Raw tables matching CSV structure exactly
-- No constraints, no cleaning — just land the data

DROP TABLE IF EXISTS raw_order_items;
DROP TABLE IF EXISTS raw_orders;
DROP TABLE IF EXISTS raw_customers;

CREATE TABLE raw_customers (
    customer_id   TEXT,
    first_name    TEXT,
    last_name     TEXT,
    email         TEXT,
    created_at    TEXT,
    country       TEXT
);

CREATE TABLE raw_orders (
    order_id      TEXT,
    customer_id   TEXT,
    order_date    TEXT,
    status        TEXT,
    total_amount  TEXT,
    currency      TEXT
);

CREATE TABLE raw_order_items (
    order_item_id TEXT,
    order_id      TEXT,
    product_id    TEXT,
    product_name  TEXT,
    category      TEXT,
    quantity      TEXT,
    unit_price    TEXT,
    total_price   TEXT
);
