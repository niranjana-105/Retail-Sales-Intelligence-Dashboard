import streamlit as st

st.set_page_config(
    page_title="Retail Sales Intelligence Dashboard",
    layout="wide"
)

st.title("🛒 Retail Sales Intelligence & Demand Forecasting Platform")

st.markdown(
"""
Welcome to the **Retail Sales Intelligence & Predictive Demand Forecasting Platform**.

This enterprise-grade application combines a **MySQL/SQLite Star Schema Data Warehouse**
with an **XGBoost Time-Series Forecasting Engine** — delivering both descriptive business
analytics and predictive demand planning in one unified dashboard.

Use the sidebar to navigate through the modules.


### Available Pages

• **Overview**: High-level KPIs, monthly trends, and regional performance

• **Sales Analysis**: Dynamic yearly filters, monthly trends, and top revenue regions

• **Customer Analysis**: Demographic segmentation (Age Bands, Couples vs Families)

• **Business Insights**: Packaging change impact analysis and annual trends

• **Channel & Market Expansion**: Omni-channel dynamics (Retail vs Shopify), demographic digital adoption, and CRUD data management

• **🤖 Demand Forecasting**: XGBoost ML forecasting pipeline — actual vs. predicted demand,
  12-week projection, feature importance, and What-If scenario simulator

### Architecture & Data Flow

```
Raw Transaction Data
      │  ETL (Python / Pandas)
      ▼
MySQL / SQLite Star Schema
(dim_region · dim_platform · dim_segment · fact_weekly_sales)
      │  SQL Window Functions (LAG · OVER · ROWS BETWEEN)
      ▼
Time-Series Feature Engineering
(Lags t-1/t-2/t-4/t-8 · Rolling Mean 4wk/8wk · Calendar Seasonality)
      │  Chronological TimeSeriesSplit (no lookahead leakage)
      ▼
XGBoost Regressor  →  Joblib Model Artifact
      │
      ▼
Streamlit Interactive Dashboard (Plotly)
```

### Technologies
- **Database**: MySQL & SQLite (dual-engine, zero-config auto-ingestion)
- **ML Stack**: XGBoost · Scikit-learn (TimeSeriesSplit) · Joblib
- **Frontend**: Streamlit · Plotly
- **Data Engineering**: Python · Pandas ETL pipeline
"""
)