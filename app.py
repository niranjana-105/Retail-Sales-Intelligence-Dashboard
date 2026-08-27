import streamlit as st

st.set_page_config(
    page_title="Retail Sales Intelligence Dashboard",
    layout="wide"
)

st.title("🛒 Retail Sales Intelligence & Analytics Dashboard")

st.markdown(
"""
Welcome to the **Retail Sales Intelligence & Analytics Dashboard**.

This enterprise-grade application provides interactive business intelligence, customer cohort analysis, and omni-channel performance analytics across multi-region retail transactions.

Use the sidebar to navigate through the dashboard modules.


### Available Pages

• **Overview**: High-level KPIs, monthly trends, and regional performance

• **Sales Analysis**: Dynamic yearly filters, monthly trends, and top revenue regions

• **Customer Analysis**: Demographic segmentation (Age Bands, Couples vs Families)

• **Business Insights**: Packaging change impact analysis and annual trends

• **Channel & Market Expansion**: Omni-channel dynamics (Retail vs Shopify), demographic digital adoption, and CRUD data management

### Architecture & Technologies

- **Database**: 4-Table Star Schema (`dim_region`, `dim_platform`, `dim_segment`, `fact_weekly_sales`)
- **SQL Engines**: MySQL & SQLite (Dual Engine with Zero-Config Auto-Ingestion)
- **Frontend**: Streamlit & Plotly Interactive Visualizations
- **Data Engineering**: Python & Pandas ETL Pipeline
"""
)