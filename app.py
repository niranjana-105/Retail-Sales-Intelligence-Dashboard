import streamlit as st

st.set_page_config(
    page_title="Data Mart Dashboard",
    layout="wide"
)

st.title("Data Mart Analytics Dashboard")

st.markdown(
"""
Welcome to the **Data Mart Analytics Dashboard**.

This dashboard provides interactive insights into the
Data Mart dataset.

Use the sidebar to navigate through the dashboard.

### Available Pages

• Overview

• Sales Analysis

• Customer Analysis

• Business Insights

### Technologies

- MySQL
- Streamlit
- Plotly
- Pandas
"""
)