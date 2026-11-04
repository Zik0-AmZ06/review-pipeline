
      
        
        
        delete from "reviews"."public"."fact_order_items" as DBT_INTERNAL_DEST
        where (order_item_id) in (
            select distinct order_item_id
            from "fact_order_items__dbt_tmp163553521858" as DBT_INTERNAL_SOURCE
        );

    

    insert into "reviews"."public"."fact_order_items" ("order_item_id", "order_id", "customer_id", "product_id", "product_name", "order_date", "status", "currency", "quantity", "unit_price", "total_price", "year", "month", "year_month")
    (
        select "order_item_id", "order_id", "customer_id", "product_id", "product_name", "order_date", "status", "currency", "quantity", "unit_price", "total_price", "year", "month", "year_month"
        from "fact_order_items__dbt_tmp163553521858"
    )
  