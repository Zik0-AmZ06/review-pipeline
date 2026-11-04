-- Staging model for customers


with source as (
    select * from "reviews"."public"."raw_customers"
),
cleaned as (
    select
        customer_id::int as customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(trim(email)) as email,
        created_at::date as created_at,
        trim(country) as country
    from source
    where customer_id ~ '^\d+$'
)
select * from cleaned