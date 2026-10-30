
  
    

  create  table "reviews"."public"."dim_product__dbt_tmp"
  
  
    as
  
  (
    -- Product dimension (latest price per product)


with stg as (
    select * from "reviews"."public"."stg_order_items"
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
  );
  