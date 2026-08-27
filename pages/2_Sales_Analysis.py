import streamlit as st
import plotly.express as px
from db import run_query

st.set_page_config(page_title="Sales Performance Analysis", layout="wide")

st.title("📈 Sales Performance Analysis")

# ==========================================================
# Year Filter
# ==========================================================

years = run_query("""
SELECT DISTINCT calendar_year
FROM fact_weekly_sales
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

st.subheader("Monthly Sales Trend")

query = """
SELECT
    f.month_number,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
WHERE f.calendar_year = %s
GROUP BY f.month_number
ORDER BY f.month_number;
"""

df = run_query(query, params=(selected_year,))

fig = px.line(
    df,
    x="month_number",
    y="total_sales",
    markers=True,
    title=f"Monthly Sales ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Region (Relational INNER JOIN)
# ==========================================================

st.subheader("Regional Performance (fact_weekly_sales JOIN dim_region)")

query = """
SELECT
    r.region_name AS region,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_region r ON f.region_id = r.region_id
WHERE f.calendar_year = %s
GROUP BY r.region_name
ORDER BY total_sales DESC;
"""

df = run_query(query, params=(selected_year,))

fig = px.bar(
    df,
    x="region",
    y="total_sales",
    color="total_sales",
    title=f"Regional Sales Breakdown ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Platform (Relational INNER JOIN)
# ==========================================================

st.subheader("Platform Revenue Share (fact_weekly_sales JOIN dim_platform)")

query = """
SELECT
    p.platform_name AS platform,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_platform p ON f.platform_id = p.platform_id
WHERE f.calendar_year = %s
GROUP BY p.platform_name;
"""

df = run_query(query, params=(selected_year,))

fig = px.pie(
    df,
    names="platform",
    values="total_sales",
    title=f"Platform Sales Contribution ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Top 10 Regions Table (Relational INNER JOIN)
# ==========================================================

st.subheader("Top Performing Regions Leaderboard")

query = """
SELECT
    r.region_name AS region,
    SUM(f.sales) AS total_sales,
    SUM(f.transactions) AS total_transactions,
    ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_transaction
FROM fact_weekly_sales f
INNER JOIN dim_region r ON f.region_id = r.region_id
WHERE f.calendar_year = %s
GROUP BY r.region_name
ORDER BY total_sales DESC
LIMIT 10;
"""

df = run_query(query, params=(selected_year,))

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
