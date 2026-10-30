-- Product dimension (latest price per product)
{{ config(materialized='table') }}

with stg as (
    select * from {{ ref('stg_order_items') }}
),
ranked as (
    select
        product_id,
        product_name,
        category,
        unit_price,
        row_number() over (partition by product_id order by unit_price desc) as rn
    from stg
)
select
    product_id,
    product_name,
    category,
    unit_price as current_price
from ranked
where rn = 1
