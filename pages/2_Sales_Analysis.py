import streamlit as st
import plotly.express as px
from db import run_query

st.title("Sales Analysis")

# ==========================================================
# Year Filter
# ==========================================================

years = run_query("""
SELECT DISTINCT calendar_year
FROM clean_weekly_sales
ORDER BY calendar_year;
""")

selected_year = st.selectbox(
    "Select Year",
    years["calendar_year"]
)

st.divider()

# ==========================================================
# Sales by Month
# ==========================================================

st.subheader("Monthly Sales")

query = f"""
SELECT
    month_number,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY month_number
ORDER BY month_number;
"""

df = run_query(query)

fig = px.line(
    df,
    x="month_number",
    y="total_sales",
    markers=True,
    title=f"Monthly Sales ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Region
# ==========================================================

st.subheader("Sales by Region")

query = f"""
SELECT
    region,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY region
ORDER BY total_sales DESC;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="region",
    y="total_sales",
    color="total_sales",
    title=f"Regional Sales ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Platform
# ==========================================================

st.subheader("Sales by Platform")

query = f"""
SELECT
    platform,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY platform;
"""

df = run_query(query)

fig = px.pie(
    df,
    names="platform",
    values="total_sales",
    title=f"Platform Sales ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Top 10 Regions
# ==========================================================

st.subheader("Top Performing Regions")

query = f"""
SELECT
    region,
    SUM(sales) AS total_sales,
    SUM(transactions) AS total_transactions,
    ROUND(AVG(avg_transaction),2) AS avg_transaction
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY region
ORDER BY total_sales DESC
LIMIT 10;
"""

df = run_query(query)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

