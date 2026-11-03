-- Real staging tables for Python loader to insert into
-- dbt will reference these as sources

DROP TABLE IF EXISTS stg_order_items CASCADE;
DROP TABLE IF EXISTS stg_orders CASCADE;
DROP TABLE IF EXISTS stg_customers CASCADE;

CREATE TABLE stg_customers (
    customer_id   INT PRIMARY KEY,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL,
    created_at    DATE NOT NULL,
    country       TEXT NOT NULL
);

CREATE TABLE stg_orders (
    order_id      INT PRIMARY KEY,
    customer_id   INT NOT NULL REFERENCES stg_customers(customer_id),
    order_date    DATE NOT NULL,
    status        TEXT NOT NULL,
    total_amount  NUMERIC NOT NULL,
    currency      TEXT NOT NULL
);

CREATE TABLE stg_order_items (
    order_item_id INT PRIMARY KEY,
    order_id      INT NOT NULL REFERENCES stg_orders(order_id),
    product_id    INT NOT NULL,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    quantity      INT NOT NULL,
    unit_price    NUMERIC NOT NULL,
    total_price   NUMERIC NOT NULL
);
