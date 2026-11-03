import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import create_engine
from datetime import datetime

st.set_page_config(page_title="E-Commerce Data Warehouse", layout="wide")

# ─── DB Connection ───
@st.cache_resource
def get_engine():
    db_url = st.secrets.get("DATABASE_URL",
                            "postgresql://review_app:IIsXAi1mcvgYNTZv@127.0.0.1:5433/reviews")
    # Force psycopg2 driver (since we have psycopg2-binary installed)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return create_engine(db_url)

@st.cache_data(ttl=300)
def run_query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, get_engine())

# ─── Queries ───
MONTHLY_REV = """
    SELECT year_month, SUM(total_price) as revenue
    FROM fact_order_items
    GROUP BY year_month
    ORDER BY year_month
"""

TOP_PRODUCTS = """
    SELECT p.product_name, SUM(f.total_price) as total_revenue, SUM(f.quantity) as total_quantity
    FROM fact_order_items f
    JOIN dim_product p ON f.product_id = p.product_id
    GROUP BY p.product_name
    ORDER BY total_revenue DESC
    LIMIT 10
"""

RETENTION_COHORT = """
    WITH first_order AS (
        SELECT customer_id, DATE_TRUNC('month', MIN(order_date))::date as cohort_month
        FROM fact_order_items
        GROUP BY customer_id
    ),
    orders_by_month AS (
        SELECT f.customer_id, DATE_TRUNC('month', f.order_date)::date as order_month
        FROM fact_order_items f
        JOIN first_order c ON f.customer_id = c.customer_id
    ),
    cohort_sizes AS (
        SELECT cohort_month, COUNT(DISTINCT customer_id) as cohort_size
        FROM first_order
        GROUP BY cohort_month
    ),
    retention AS (
        SELECT c.cohort_month, o.order_month, COUNT(DISTINCT o.customer_id) as active_customers
        FROM first_order c
        JOIN orders_by_month o ON c.customer_id = o.customer_id
        GROUP BY c.cohort_month, o.order_month
    )
    SELECT r.cohort_month, r.order_month, r.active_customers, cs.cohort_size,
           ROUND(r.active_customers::numeric / cs.cohort_size * 100, 1) as retention_pct
    FROM retention r
    JOIN cohort_sizes cs ON r.cohort_month = cs.cohort_month
    ORDER BY r.cohort_month, r.order_month
"""

RETURNING = """
    SELECT 
        COUNT(DISTINCT customer_id) as total_customers,
        COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END) as returning_customers,
        ROUND(COUNT(DISTINCT CASE WHEN order_count > 1 THEN customer_id END)::numeric / COUNT(DISTINCT customer_id) * 100, 1) as return_rate_pct
    FROM (
        SELECT customer_id, COUNT(DISTINCT order_id) as order_count
        FROM fact_order_items
        GROUP BY customer_id
    ) c
"""

CURRENCY_BREAKDOWN = """
    SELECT currency, COUNT(DISTINCT order_id) as orders, SUM(total_price) as revenue
    FROM fact_order_items
    GROUP BY currency
    ORDER BY revenue DESC
"""

# ─── UI ───
st.title("📊 E-Commerce Data Warehouse Dashboard")
st.caption(f"PostgreSQL 17 · dbt · Evidence · Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Load data
monthly = run_query(MONTHLY_REV)
top_prod = run_query(TOP_PRODUCTS)
cohort = run_query(RETENTION_COHORT)
returning = run_query(RETURNING)
currency = run_query(CURRENCY_BREAKDOWN)

# KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"${monthly['revenue'].sum():,.2f}")
k2.metric("Total Customers", int(returning['total_customers'].iloc[0]))
k3.metric("Returning Customers", int(returning['returning_customers'].iloc[0]))
k4.metric("Return Rate", f"{returning['return_rate_pct'].iloc[0]}%")

st.divider()

# Monthly Revenue
st.subheader("📈 Monthly Revenue")
fig1 = px.bar(monthly, x="year_month", y="revenue", title="Monthly Revenue (All Currencies)",
              labels={"revenue": "Revenue ($)", "year_month": "Month"})
fig1.update_layout(yaxis_tickprefix="$")
st.plotly_chart(fig1, use_container_width=True)

# Top Products
st.subheader("🏆 Top 10 Products by Revenue")
fig2 = px.bar(top_prod, x="product_name", y="total_revenue", title="Top Products",
              labels={"total_revenue": "Revenue ($)", "product_name": "Product"},
              color="total_revenue", color_continuous_scale="Blues")
fig2.update_layout(yaxis_tickprefix="$", xaxis_tickangle=-45)
st.plotly_chart(fig2, use_container_width=True)

# Two columns
col1, col2 = st.columns(2)

with col1:
    # Retention Cohort Heatmap
    st.subheader("👥 Customer Retention Cohort")
    if not cohort.empty:
        pivot = cohort.pivot(index="cohort_month", columns="order_month", values="retention_pct")
        fig3 = px.imshow(pivot, title="Retention by Cohort (%)", 
                         color_continuous_scale="Blues", aspect="auto",
                         labels=dict(x="Order Month", y="Cohort Month", color="Retention %"))
        fig3.update_layout(height=400)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Not enough data for cohort analysis")

with col2:
    # Currency Breakdown
    st.subheader("💱 Revenue by Currency")
    fig4 = px.pie(currency, values="revenue", names="currency", title="Revenue by Currency")
    st.plotly_chart(fig4, use_container_width=True)

    # Returning Customers
    st.subheader("🔄 Returning Customers")
    st.metric("Return Rate", f"{returning['return_rate_pct'].iloc[0]}%")
    st.write(f"**Total Customers:** {int(returning['total_customers'].iloc[0])}")
    st.write(f"**Returning:** {int(returning['returning_customers'].iloc[0])}")

st.divider()
st.caption("Built with Streamlit · Data from PostgreSQL + dbt · [GitHub Repo](https://github.com)")
