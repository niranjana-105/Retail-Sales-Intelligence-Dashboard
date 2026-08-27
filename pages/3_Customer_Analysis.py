import streamlit as st
import plotly.express as px
from db import run_query

st.set_page_config(page_title="Customer Demographic Analysis", layout="wide")

st.title("👥 Customer Demographic Analysis")

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
# Sales by Demographic (Relational INNER JOIN)
# ==========================================================

st.subheader("Sales by Demographic (fact_weekly_sales JOIN dim_segment)")

query = """
SELECT
    s.demographic,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_segment s ON f.segment_id = s.segment_id
WHERE f.calendar_year = %s AND s.demographic != 'unknown'
GROUP BY s.demographic;
"""

df = run_query(query, params=(selected_year,))

fig = px.bar(
    df,
    x="demographic",
    y="total_sales",
    color="demographic",
    title=f"Sales by Family Demographic ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Age Band (Relational INNER JOIN)
# ==========================================================

st.subheader("Sales by Age Band (fact_weekly_sales JOIN dim_segment)")

query = """
SELECT
    s.age_band,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_segment s ON f.segment_id = s.segment_id
WHERE f.calendar_year = %s AND s.age_band != 'unknown'
GROUP BY s.age_band;
"""

df = run_query(query, params=(selected_year,))

fig = px.pie(
    df,
    names="age_band",
    values="total_sales",
    title=f"Revenue Distribution by Age Cohort ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Customer Type Performance
# ==========================================================

st.subheader("Customer Type Performance (New vs Existing vs Guest)")

query = """
SELECT
    f.customer_type,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
WHERE f.calendar_year = %s
GROUP BY f.customer_type
ORDER BY total_sales DESC;
"""

df = run_query(query, params=(selected_year,))

fig = px.bar(
    df,
    x="customer_type",
    y="total_sales",
    color="total_sales",
    title=f"Customer Type Revenue ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Customer Segment Summary (Relational INNER JOIN)
# ==========================================================

st.subheader("Demographic & Age Band Segment Matrix")

query = """
SELECT
    s.demographic,
    s.age_band,
    SUM(f.sales) AS total_sales,
    SUM(f.transactions) AS total_transactions,
    ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_transaction
FROM fact_weekly_sales f
INNER JOIN dim_segment s ON f.segment_id = s.segment_id
WHERE f.calendar_year = %s AND s.segment_code != 'unknown'
GROUP BY s.demographic, s.age_band
ORDER BY total_sales DESC;
"""

df = run_query(query, params=(selected_year,))

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
