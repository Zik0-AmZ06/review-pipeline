-- Business questions for Stage 1

-- 1. Monthly revenue (using order_items total_price, converted to USD via simple assumption)
--    Note: In reality you'd use exchange rates. Here we'll note the currency issue.
WITH revenue_usd AS (
    SELECT
        date_trunc('month', oi.order_date::date) AS month,
        SUM(oi.total_price::numeric) AS revenue
    FROM (
        SELECT
            o.order_id,
            o.order_date,
            oi.total_price
        FROM raw_orders o
        JOIN raw_order_items oi ON o.order_id = oi.order_id
        WHERE o.status = 'completed'
    ) oi
    GROUP BY 1
    ORDER BY 1
)
SELECT to_char(month, 'YYYY-MM') AS month, revenue
FROM revenue_usd;

-- 2. Top 5 products by total revenue
SELECT
    oi.product_name,
    SUM(oi.total_price::numeric) AS total_revenue,
    SUM(oi.quantity::int) AS total_quantity
FROM raw_order_items oi
JOIN raw_orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY oi.product_name
ORDER BY total_revenue DESC
LIMIT 5;

-- 3. Customers with no orders
SELECT c.customer_id, c.first_name, c.last_name, c.email
FROM raw_customers c
LEFT JOIN raw_orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL
ORDER BY c.customer_id;
