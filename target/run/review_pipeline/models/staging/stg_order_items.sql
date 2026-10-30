
  create view "reviews"."public"."stg_order_items__dbt_tmp"
    
    
  as (
    -- Staging model for order items
with source as (
    select * from "reviews"."public"."raw_order_items"
),
cleaned as (
    select
        order_item_id::int as order_item_id,
        order_id::int as order_id,
        product_id::int as product_id,
        trim(product_name) as product_name,
        trim(category) as category,
        quantity::int as quantity,
        unit_price::numeric as unit_price,
        total_price::numeric as total_price
    from source
    where order_item_id ~ '^\d+$'
      and order_id ~ '^\d+$'
      and product_id ~ '^\d+$'
)
select * from cleaned
  );