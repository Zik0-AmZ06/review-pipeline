-- Date dimension


with bounds as (
    select
        min(order_date)::date as min_dt,
        max(order_date)::date as max_dt
    from "reviews"."public"."stg_orders"
),
dates as (
    select generate_series(min_dt, max_dt, interval '1 day')::date as date_key
    from bounds
)
select
    date_key,
    extract(year from date_key)::int as year,
    extract(month from date_key)::int as month,
    extract(day from date_key)::int as day,
    to_char(date_key, 'YYYY-MM') as year_month,
    to_char(date_key, 'Day') as day_name,
    case when extract(isodow from date_key) in (6,7) then true else false end as is_weekend
from dates