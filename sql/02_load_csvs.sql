-- Load CSVs into raw tables
-- Run from psql: \i sql/02_load_csvs.sql
-- Assumes CSVs are in ../data/ relative to this file

\copy raw_customers(customer_id, first_name, last_name, email, created_at, country) FROM 'C:/Users/amouz/source/repos/review-pipeline/data/customers.csv' WITH (FORMAT csv, HEADER true);
\copy raw_orders(order_id, customer_id, order_date, status, total_amount, currency) FROM 'C:/Users/amouz/source/repos/review-pipeline/data/orders.csv' WITH (FORMAT csv, HEADER true);
\copy raw_order_items(order_item_id, order_id, product_id, product_name, category, quantity, unit_price, total_price) FROM 'C:/Users/amouz/source/repos/review-pipeline/data/order_items.csv' WITH (FORMAT csv, HEADER true);

SELECT 'raw_customers' AS table_name, COUNT(*) FROM raw_customers
UNION ALL SELECT 'raw_orders', COUNT(*) FROM raw_orders
UNION ALL SELECT 'raw_order_items', COUNT(*) FROM raw_order_items;