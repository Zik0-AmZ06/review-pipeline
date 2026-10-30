---
title: E-Commerce Data Warehouse Dashboard
description: Monthly revenue, top products, customer retention
---

# 📊 E-Commerce Data Warehouse Dashboard

This dashboard is built on a PostgreSQL data warehouse with dbt transformations.

## 📈 Monthly Revenue

```sql monthly_revenue
SELECT * FROM ${monthly_revenue}
```

<BarChart
    data={monthly_revenue}
    x=year_month
    y=revenue
    title="Monthly Revenue (All Currencies)"
    yFmt="usd"
/>

## 🏆 Top 10 Products by Revenue

```sql top_products
SELECT * FROM ${top_products}
```

<BarChart
    data={top_products}
    x=product_name
    y=total_revenue
    title="Top Products"
    yFmt="usd"
    sort=-y
/>

## 👥 Customer Retention Cohort

```sql customer_cohort
SELECT * FROM ${customer_cohort}
```

<Heatmap
    data={customer_cohort}
    x=order_month
    y=cohort_month
    value=retention_pct
    title="Retention by Cohort (%)"
    colorScale="blues"
/>

## 🔄 Returning Customers

```sql returning_customers
SELECT * FROM ${returning_customers}
```

<BigValue
    data={returning_customers}
    value=return_rate_pct
    title="Customer Return Rate"
    suffix="%"
/>

## 💱 Revenue by Currency

```sql currency_breakdown
SELECT * FROM ${currency_breakdown}
```

<PieChart
    data={currency_breakdown}
    labels=currency
    values=revenue
    title="Revenue by Currency"
/>

---
*Data updated: ${new Date().toLocaleString()}*
*Warehouse: PostgreSQL 17 | Transformations: dbt | Dashboard: Evidence*
