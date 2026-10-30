-- Stage 2: Data Modeling - Cleaned tables, dimensions, fact
-- Run: psql -h 127.0.0.1 -p 5433 -U review_app -d reviews -f sql/04_create_cleaned_tables.sql

-- ============================================================
-- 1. STAGING TABLES (proper types, deduplication)
-- ============================================================

DROP TABLE IF EXISTS stg_customers;
CREATE TABLE stg_customers AS
SELECT
    customer_id::int       AS customer_id,
    trim(first_name)       AS first_name,
    trim(last_name)        AS last_name,
    lower(trim(email))     AS email,
    created_at::date       AS created_at,
    trim(country)          AS country
FROM raw_customers
WHERE customer_id ~ '^\d+$';

DROP TABLE IF EXISTS stg_orders;
CREATE TABLE stg_orders AS
SELECT
    order_id::int          AS order_id,
    customer_id::int       AS customer_id,
    order_date::date       AS order_date,
    lower(trim(status))    AS status,
    total_amount::numeric  AS total_amount,
    upper(trim(currency))  AS currency
FROM raw_orders
WHERE order_id ~ '^\d+$'
  AND customer_id ~ '^\d+$';

DROP TABLE IF EXISTS stg_order_items;
CREATE TABLE stg_order_items AS
SELECT
    order_item_id::int     AS order_item_id,
    order_id::int          AS order_id,
    product_id::int        AS product_id,
    trim(product_name)     AS product_name,
    trim(category)         AS category,
    quantity::int          AS quantity,
    unit_price::numeric    AS unit_price,
    total_price::numeric   AS total_price
FROM raw_order_items
WHERE order_item_id ~ '^\d+$'
  AND order_id ~ '^\d+$'
  AND product_id ~ '^\d+$';

-- ============================================================
-- 2. DIMENSION TABLES
-- ============================================================

-- dim_customer: one row per customer
DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer AS
SELECT
    customer_id,
    first_name,
    last_name,
    email,
    created_at,
    country,
    CASE
        WHEN country IN ('USA','Canada') THEN 'North America'
        WHEN country IN ('UK','Germany','France') THEN 'Europe'
        WHEN country IN ('Australia') THEN 'APAC'
        ELSE 'Other'
    END AS region
FROM stg_customers;

ALTER TABLE dim_customer ADD PRIMARY KEY (customer_id);

-- dim_product: one row per product (latest known price/category)
DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product AS
WITH ranked AS (
    SELECT
        product_id,
        product_name,
        category,
        unit_price,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY unit_price DESC) AS rn
    FROM stg_order_items
)
SELECT
    product_id,
    product_name,
    category,
    unit_price AS current_price
FROM ranked
WHERE rn = 1;

ALTER TABLE dim_product ADD PRIMARY KEY (product_id);

-- dim_date: date dimension for slicing
DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date AS
WITH bounds AS (
    SELECT
        min(order_date)::date AS min_dt,
        max(order_date)::date AS max_dt
    FROM stg_orders
),
dates AS (
    SELECT generate_series(min_dt, max_dt, interval '1 day')::date AS date_key
    FROM bounds
)
SELECT
    date_key,
    EXTRACT(year FROM date_key)::int       AS year,
    EXTRACT(month FROM date_key)::int      AS month,
    EXTRACT(day FROM date_key)::int        AS day,
    TO_CHAR(date_key, 'YYYY-MM')           AS year_month,
    TO_CHAR(date_key, 'Day')               AS day_name,
    CASE WHEN EXTRACT(isodow FROM date_key) IN (6,7) THEN true ELSE false END AS is_weekend
FROM dates;

ALTER TABLE dim_date ADD PRIMARY KEY (date_key);

-- ============================================================
-- 3. FACT TABLE
-- ============================================================

DROP TABLE IF EXISTS fact_order_items;
CREATE TABLE fact_order_items AS
SELECT
    oi.order_item_id,
    o.order_id,
    o.customer_id,
    oi.product_id,
    o.order_date,
    o.status,
    o.currency,
    oi.quantity,
    oi.unit_price,
    oi.total_price,
    d.year,
    d.month,
    d.year_month
FROM stg_order_items oi
JOIN stg_orders o ON oi.order_id = o.order_id
JOIN dim_date d ON o.order_date = d.date_key
WHERE o.status = 'completed';

ALTER TABLE fact_order_items ADD PRIMARY KEY (order_item_id);

-- ============================================================
-- 4. VALIDATION QUERIES
-- ============================================================

-- Row counts
SELECT 'stg_customers' AS table_name, COUNT(*) FROM stg_customers
UNION ALL SELECT 'stg_orders', COUNT(*) FROM stg_orders
UNION ALL SELECT 'stg_order_items', COUNT(*) FROM stg_order_items
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL SELECT 'fact_order_items', COUNT(*) FROM fact_order_items;

-- Revenue reconciliation: fact vs raw (completed orders only)
WITH fact_rev AS (
    SELECT SUM(total_price) AS revenue FROM fact_order_items
),
raw_rev AS (
    SELECT SUM(oi.total_price::numeric) AS revenue
    FROM raw_order_items oi
    JOIN raw_orders o ON oi.order_id = o.order_id
    WHERE o.status = 'completed'
)
SELECT
    'fact' AS source, revenue FROM fact_rev
UNION ALL
SELECT 'raw', revenue FROM raw_rev;

-- Customer count check
SELECT 'dim_customer' AS source, COUNT(*) FROM dim_customer
UNION ALL
SELECT 'raw_customers', COUNT(*) FROM raw_customers;

-- Product count check
SELECT 'dim_product' AS source, COUNT(*) FROM dim_product
UNION ALL
SELECT 'distinct raw products', COUNT(DISTINCT product_id) FROM raw_order_items;

-- Date range check
SELECT min(date_key) AS min_date, max(date_key) AS max_date FROM dim_date;
