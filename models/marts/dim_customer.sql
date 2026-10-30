-- Customer dimension
{{ config(materialized='table') }}

with stg as (
    select * from {{ ref('stg_customers') }}
)
select
    customer_id,
    first_name,
    last_name,
    email,
    created_at,
    country,
    case
        when country in ('USA','Canada') then 'North America'
        when country in ('UK','Germany','France') then 'Europe'
        when country in ('Australia') then 'APAC'
        else 'Other'
    end as region
from stg
