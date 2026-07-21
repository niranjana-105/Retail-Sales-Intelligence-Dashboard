import streamlit as st
import plotly.express as px
from db import run_query

st.title("Overview")

# ==========================================================
# KPI Cards
# ==========================================================

kpi_query = """
SELECT
    SUM(sales) AS total_sales,
    SUM(transactions) AS total_transactions,
    ROUND(AVG(avg_transaction),2) AS avg_transaction,
    COUNT(DISTINCT region) AS total_regions
FROM clean_weekly_sales;
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
        "Avg Transaction",
        f"${kpi.iloc[0]['avg_transaction']:.2f}"
    )

with col4:
    st.metric(
        "Regions",
        int(kpi.iloc[0]['total_regions'])
    )

st.divider()

# ==========================================================
# Monthly Sales Trend
# ==========================================================

st.subheader("Monthly Sales Trend")

monthly_query = """
SELECT
    month_number,
    SUM(sales) AS sales
FROM clean_weekly_sales
GROUP BY month_number
ORDER BY month_number;
"""

monthly_df = run_query(monthly_query)

fig = px.line(
    monthly_df,
    x="month_number",
    y="sales",
    markers=True,
    title="Monthly Sales"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Region
# ==========================================================

st.subheader("Sales by Region")

region_query = """
SELECT
    region,
    SUM(sales) AS sales
FROM clean_weekly_sales
GROUP BY region
ORDER BY sales DESC;
"""

region_df = run_query(region_query)

fig = px.bar(
    region_df,
    x="region",
    y="sales",
    title="Sales by Region"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Platform Distribution
# ==========================================================

st.subheader("Retail vs Shopify")

platform_query = """
SELECT
    platform,
    SUM(sales) AS sales
FROM clean_weekly_sales
GROUP BY platform;
"""

platform_df = run_query(platform_query)

fig = px.pie(
    platform_df,
    names="platform",
    values="sales",
    title="Platform Distribution"
)

st.plotly_chart(fig, use_container_width=True)