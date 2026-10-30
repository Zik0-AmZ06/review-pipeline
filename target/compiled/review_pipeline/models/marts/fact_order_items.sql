-- Fact table: completed order lines with dimensions


with stg_items as (
    select * from "reviews"."public"."stg_order_items"
),
stg_orders as (
    select * from "reviews"."public"."stg_orders"
),
dim_date as (
    select * from "reviews"."public"."dim_date"
)
select
    oi.order_item_id,
    o.order_id,
    o.customer_id,
    oi.product_id,
    oi.product_name,
    o.order_date,
    o.status,
    o.currency,
    oi.quantity,
    oi.unit_price,
    oi.total_price,
    d.year,
    d.month,
    d.year_month
from stg_items oi
         join stg_orders o on oi.order_id = o.order_id
         join dim_date d on o.order_date = d.date_key
where o.status = 'completed'
    