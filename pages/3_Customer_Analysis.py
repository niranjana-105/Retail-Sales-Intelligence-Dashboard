import streamlit as st
import plotly.express as px
from db import run_query

st.title("Customer Analysis")

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
# Sales by Demographic
# ==========================================================

st.subheader("Sales by Demographic")

query = f"""
SELECT
    demographic,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY demographic;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="demographic",
    y="total_sales",
    color="demographic",
    title=f"Sales by Demographic ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Sales by Age Band
# ==========================================================

st.subheader("Sales by Age Band")

query = f"""
SELECT
    age_band,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY age_band;
"""

df = run_query(query)

fig = px.pie(
    df,
    names="age_band",
    values="total_sales",
    title=f"Sales by Age Band ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Customer Type Performance
# ==========================================================

st.subheader("Customer Type Performance")

query = f"""
SELECT
    customer_type,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY customer_type
ORDER BY total_sales DESC;
"""

df = run_query(query)

fig = px.bar(
    df,
    x="customer_type",
    y="total_sales",
    color="total_sales",
    title=f"Customer Type Performance ({selected_year})"
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# Customer Segment Summary
# ==========================================================

st.subheader("Customer Segment Summary")

query = f"""
SELECT
    demographic,
    age_band,
    SUM(sales) AS total_sales,
    SUM(transactions) AS total_transactions,
    ROUND(AVG(avg_transaction),2) AS avg_transaction
FROM clean_weekly_sales
WHERE calendar_year = {selected_year}
GROUP BY demographic, age_band
ORDER BY total_sales DESC;
"""

df = run_query(query)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
