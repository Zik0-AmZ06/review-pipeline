-- Staging model for orders
{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'raw_orders') }}
),
cleaned as (
    select
        order_id::int as order_id,
        customer_id::int as customer_id,
        order_date::date as order_date,
        lower(trim(status)) as status,
        total_amount::numeric as total_amount,
        upper(trim(currency)) as currency
    from source
    where order_id ~ '^\d+$'
      and customer_id ~ '^\d+$'
)
select * from cleaned
