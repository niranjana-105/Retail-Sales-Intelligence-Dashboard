import streamlit as st
import plotly.express as px
from db import run_query

st.set_page_config(page_title="Executive Overview", layout="wide")

st.title("📊 Executive Overview")

# ==========================================================
# KPI Cards
# ==========================================================

kpi_query = """
SELECT
    SUM(f.sales) AS total_sales,
    SUM(f.transactions) AS total_transactions,
    ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_transaction,
    COUNT(DISTINCT f.region_id) AS total_regions
FROM fact_weekly_sales f;
"""

kpi = run_query(kpi_query)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Sales",
        f"${kpi.iloc[0]['total_sales']:,.0f}"
    )

with col2:
    st.metric(
        "Transactions",
        f"{int(kpi.iloc[0]['total_transactions']):,}"
    )

with col3:
    st.metric(
        "Avg Order Value",
        f"${kpi.iloc[0]['avg_transaction']:.2f}"
    )

with col4:
    st.metric(
        "Regions Covered",
        int(kpi.iloc[0]['total_regions'])
    )

st.divider()

# ==========================================================
# Monthly Sales Trend
# ==========================================================

st.subheader("Monthly Sales Trajectory")

monthly_query = """
SELECT
    f.month_number,
    SUM(f.sales) AS sales
FROM fact_weekly_sales f
GROUP BY f.month_number
ORDER BY f.month_number;
"""

monthly_df = run_query(monthly_query)

fig = px.line(
    monthly_df,
    x="month_number",
    y="sales",
    markers=True,
    title="Aggregate Monthly Sales Trajectory"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Region (Multi-Table JOIN)
# ==========================================================

st.subheader("Sales by Region (Relational JOIN)")

region_query = """
SELECT
    r.region_name AS region,
    SUM(f.sales) AS sales
FROM fact_weekly_sales f
INNER JOIN dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name
ORDER BY sales DESC;
"""

region_df = run_query(region_query)

fig = px.bar(
    region_df,
    x="region",
    y="sales",
    color="sales",
    title="Regional Revenue Breakdown"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Platform Distribution (Multi-Table JOIN)
# ==========================================================

st.subheader("Platform Distribution (Retail vs Shopify)")

platform_query = """
SELECT
    p.platform_name AS platform,
    SUM(f.sales) AS sales
FROM fact_weekly_sales f
INNER JOIN dim_platform p ON f.platform_id = p.platform_id
GROUP BY p.platform_name;
"""

platform_df = run_query(platform_query)

fig = px.pie(
    platform_df,
    names="platform",
    values="sales",
    title="Revenue Distribution by Sales Channel"
)

st.plotly_chart(fig, use_container_width=True)