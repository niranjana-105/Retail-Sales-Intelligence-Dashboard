import streamlit as st
import plotly.express as px
from db import run_query

st.title("Business Insights")

st.markdown("""
This page summarizes key business insights derived from the
Data Mart case study.
""")

st.divider()

# ==========================================================
# Insight 1 : Sales Before vs After Packaging Change
# ==========================================================

st.subheader("Sales Before vs After Packaging Change")

query = """
WITH change_week AS (
    SELECT 25 AS change_week_num
)

SELECT
CASE
    WHEN week_number < (SELECT change_week_num FROM change_week)
        THEN 'Before Change'
    ELSE 'After Change'
END AS period,

SUM(sales) AS total_sales

FROM clean_weekly_sales

WHERE calendar_year = 2020

GROUP BY period;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="period",
    y="total_sales",
    color="period",
    title="Packaging Change Impact (2020)"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==========================================================
# Insight 2 : Top Revenue Regions
# ==========================================================

st.subheader("Top Revenue Regions")

query = """
SELECT
region,
SUM(sales) AS total_sales
FROM clean_weekly_sales
GROUP BY region
ORDER BY total_sales DESC
LIMIT 5;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="region",
    y="total_sales",
    color="total_sales",
    title="Top 5 Revenue Regions"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==========================================================
# Insight 3 : Best Customer Segments
# ==========================================================

st.subheader("Highest Revenue Customer Segments")

query = """
SELECT
demographic,
age_band,
SUM(sales) AS total_sales
FROM clean_weekly_sales
GROUP BY demographic, age_band
ORDER BY total_sales DESC;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="age_band",
    y="total_sales",
    color="demographic",
    barmode="group",
    title="Revenue by Customer Segment"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==========================================================
# Insight 4 : Year-over-Year Sales
# ==========================================================

st.subheader("Year-over-Year Sales")

query = """
SELECT
calendar_year,
SUM(sales) AS total_sales
FROM clean_weekly_sales
GROUP BY calendar_year
ORDER BY calendar_year;
"""

df = run_query(query)

fig = px.line(
    df,
    x="calendar_year",
    y="total_sales",
    markers=True,
    title="Annual Sales Trend"
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ==========================================================
# Summary Table
# ==========================================================

st.subheader("Business Summary")

query = """
SELECT
region,
SUM(sales) AS sales,
SUM(transactions) AS transactions,
ROUND(AVG(avg_transaction),2) AS avg_transaction
FROM clean_weekly_sales
GROUP BY region
ORDER BY sales DESC;
"""

df = run_query(query)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

csv = df.to_csv(index=False).encode("utf-8")

