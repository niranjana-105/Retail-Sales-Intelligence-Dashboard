import streamlit as st
import plotly.express as px
from db import run_query

st.set_page_config(page_title="Executive Business Insights", layout="wide")

st.title("💡 Executive Business Insights")

st.markdown("""
Strategic business intelligence evaluating the **2020 Sustainable Packaging Policy Rollout**, regional revenue distributions, and multi-year trajectory analysis.
""")

st.divider()

# ==========================================================
# Insight 1 : Sales Before vs After Packaging Change
# ==========================================================

st.subheader("📦 Packaging Change Policy Impact (2020)")

window_choice = st.radio(
    "Select Comparison Window:",
    [
        "12-Week Window (Weeks 13–24 vs Weeks 25–36 - Recommended)",
        "4-Week Window (Weeks 21–24 vs Weeks 25–28 - Immediate Impact)"
    ],
    horizontal=True
)

if "4-Week" in window_choice:
    where_filter = "f.calendar_year = 2020 AND f.week_number BETWEEN 21 AND 28"
    before_label = "Before Change (Weeks 21–24)"
    after_label = "After Change (Weeks 25–28)"
    case_stmt = f"""
    CASE
        WHEN f.week_number BETWEEN 21 AND 24 THEN '{before_label}'
        ELSE '{after_label}'
    END
    """
else:
    where_filter = "f.calendar_year = 2020 AND f.week_number BETWEEN 13 AND 36"
    before_label = "Before Change (Weeks 13–24)"
    after_label = "After Change (Weeks 25–36)"
    case_stmt = f"""
    CASE
        WHEN f.week_number BETWEEN 13 AND 24 THEN '{before_label}'
        ELSE '{after_label}'
    END
    """

query_packaging = f"""
SELECT
    {case_stmt} AS period,
    SUM(f.sales) AS total_sales,
    SUM(f.transactions) AS total_transactions,
    ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_transaction
FROM fact_weekly_sales f
WHERE {where_filter}
GROUP BY period
ORDER BY period DESC;
"""

df_packaging = run_query(query_packaging)

# Calculate Deltas
before_row = df_packaging[df_packaging["period"] == before_label]
after_row = df_packaging[df_packaging["period"] == after_label]

if not before_row.empty and not after_row.empty:
    before_sales = float(before_row["total_sales"].iloc[0])
    after_sales = float(after_row["total_sales"].iloc[0])
    sales_diff = after_sales - before_sales
    sales_pct = (sales_diff / before_sales) * 100.0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pre-Rollout Sales", f"${before_sales:,.0f}")
    with col2:
        st.metric("Post-Rollout Sales", f"${after_sales:,.0f}")
    with col3:
        st.metric(
            "Net Revenue Impact (Variance)",
            f"${sales_diff:+,.0f}",
            delta=f"{sales_pct:+.2f}% Growth",
            delta_color="normal"
        )

# Scaled Bar Chart
min_val = df_packaging["total_sales"].min()
max_val = df_packaging["total_sales"].max()
y_lower = min_val - (max_val - min_val) * 1.5 if (max_val - min_val) > 0 else min_val * 0.9
y_upper = max_val + (max_val - min_val) * 0.5 if (max_val - min_val) > 0 else max_val * 1.1

# Format display labels
df_packaging["sales_display"] = df_packaging["total_sales"].apply(lambda v: f"${v:,.0f} (${v/1e9:.2f}B)")

fig_pack = px.bar(
    df_packaging,
    x="period",
    y="total_sales",
    color="period",
    text="sales_display",
    title="Sales Revenue: Pre vs Post Sustainable Packaging Intervention (Rescaled Focus)",
    labels={"period": "Policy Period", "total_sales": "Total Sales ($)"},
    color_discrete_sequence=["#1f77b4", "#aec7e8"]
)

fig_pack.update_traces(textposition="outside")
fig_pack.update_layout(
    yaxis=dict(
        range=[max(0, y_lower), y_upper],
        title="Total Sales ($)"
    ),
    showlegend=False
)

st.plotly_chart(fig_pack, use_container_width=True)

st.divider()

# ==========================================================
# Insight 2 : Top Revenue Regions (Relational INNER JOIN)
# ==========================================================

st.subheader("🌍 Top 5 Revenue Generating Regions (fact_weekly_sales JOIN dim_region)")

query_regions = """
SELECT
    r.region_name AS region,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_region r ON f.region_id = r.region_id
GROUP BY r.region_name
ORDER BY total_sales DESC
LIMIT 5;
"""

df_regions = run_query(query_regions)
df_regions["sales_display"] = df_regions["total_sales"].apply(lambda v: f"${v/1e9:.2f}B")

fig_reg = px.bar(
    df_regions,
    x="region",
    y="total_sales",
    color="total_sales",
    text="sales_display",
    title="Top 5 Global Revenue Regions",
    labels={"region": "Region", "total_sales": "Total Revenue ($)"}
)
fig_reg.update_traces(textposition="outside")
st.plotly_chart(fig_reg, use_container_width=True)

st.divider()

# ==========================================================
# Insight 3 : Best Customer Segments (Relational INNER JOIN)
# ==========================================================

st.subheader("👥 Highest Revenue Customer Cohorts (fact_weekly_sales JOIN dim_segment)")

query_segments = """
SELECT
    s.demographic,
    s.age_band,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
INNER JOIN dim_segment s ON f.segment_id = s.segment_id
WHERE s.segment_code != 'unknown'
GROUP BY s.demographic, s.age_band
ORDER BY total_sales DESC;
"""

df_segments = run_query(query_segments)

fig_seg = px.bar(
    df_segments,
    x="age_band",
    y="total_sales",
    color="demographic",
    barmode="group",
    title="Revenue Generated by Customer Demographic & Age Cohort",
    labels={"age_band": "Age Band", "total_sales": "Revenue ($)", "demographic": "Family Type"}
)

st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

# ==========================================================
# Insight 4 : Year-over-Year Sales
# ==========================================================

st.subheader("📈 Multi-Year Annual Revenue Trajectory")

query_yoy = """
SELECT
    f.calendar_year,
    SUM(f.sales) AS total_sales
FROM fact_weekly_sales f
GROUP BY f.calendar_year
ORDER BY f.calendar_year;
"""

df_yoy = run_query(query_yoy)
df_yoy["sales_display"] = df_yoy["total_sales"].apply(lambda v: f"${v/1e9:.2f}B")

min_yoy = df_yoy["total_sales"].min()
max_yoy = df_yoy["total_sales"].max()

fig_yoy = px.line(
    df_yoy,
    x="calendar_year",
    y="total_sales",
    text="sales_display",
    markers=True,
    title="Annual Sales Trajectory (2018 - 2020)",
    labels={"calendar_year": "Year", "total_sales": "Total Sales ($)"}
)
fig_yoy.update_traces(textposition="top center")
fig_yoy.update_layout(
    yaxis=dict(range=[min_yoy * 0.90, max_yoy * 1.08])
)

st.plotly_chart(fig_yoy, use_container_width=True)
