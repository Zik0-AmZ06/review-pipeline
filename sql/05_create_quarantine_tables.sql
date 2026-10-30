-- Quarantine tables for bad data
DROP TABLE IF EXISTS qtn_customers;
CREATE TABLE qtn_customers (
    customer_id    TEXT,
    first_name     TEXT,
    last_name      TEXT,
    email          TEXT,
    created_at     TEXT,
    country        TEXT,
    error_code     TEXT,
    error_detail   TEXT,
    loaded_at      TIMESTAMPTZ DEFAULT now()
);

DROP TABLE IF EXISTS qtn_orders;
CREATE TABLE qtn_orders (
    order_id       TEXT,
    customer_id    TEXT,
    order_date     TEXT,
    status         TEXT,
    total_amount   TEXT,
    currency       TEXT,
    error_code     TEXT,
    error_detail   TEXT,
    loaded_at      TIMESTAMPTZ DEFAULT now()
);

DROP TABLE IF EXISTS qtn_order_items;
CREATE TABLE qtn_order_items (
    order_item_id  TEXT,
    order_id       TEXT,
    product_id     TEXT,
    product_name   TEXT,
    category       TEXT,
    quantity       TEXT,
    unit_price     TEXT,
    total_price    TEXT,
    error_code     TEXT,
    error_detail   TEXT,
    loaded_at      TIMESTAMPTZ DEFAULT now()
);

-- Indexes for querying
CREATE INDEX IF NOT EXISTS idx_qtn_customers_error ON qtn_customers(error_code);
CREATE INDEX IF NOT EXISTS idx_qtn_orders_error ON qtn_orders(error_code);
CREATE INDEX IF NOT EXISTS idx_qtn_order_items_error ON qtn_order_items(error_code);
