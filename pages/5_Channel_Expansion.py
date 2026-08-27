import streamlit as st
import plotly.express as px
from datetime import datetime
from db import run_query, execute_non_query

st.set_page_config(
    page_title="Channel & Market Expansion",
    layout="wide"
)

st.title("🌐 Channel & Market Expansion Analysis")

st.markdown("""
Strategic Business Intelligence evaluating **Omni-Channel Market Dynamics** across **Physical Retail** and **Shopify E-Commerce**. 
Analyzes channel revenue contribution, regional digital penetration, demographic purchasing affinity, and Average Order Value (AOV).
""")

st.divider()

tab1, tab2, tab3 = st.tabs([
    "📈 Regional Channel Performance",
    "👥 Demographic Channel Affinity",
    "🔧 Data Management (CRUD)"
])

# ==========================================================
# TAB 1: Regional Channel Performance
# ==========================================================
with tab1:
    st.subheader("Retail vs. Shopify Regional Revenue & Market Share")

    query_regional_channel = """
    WITH channel_summary AS (
        SELECT
            r.region_name,
            p.platform_name,
            SUM(f.sales) AS total_revenue,
            SUM(f.transactions) AS total_transactions,
            ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_order_value
        FROM fact_weekly_sales f
        INNER JOIN dim_region r ON f.region_id = r.region_id
        INNER JOIN dim_platform p ON f.platform_id = p.platform_id
        GROUP BY r.region_name, p.platform_name
    )
    SELECT
        region_name,
        platform_name,
        total_revenue,
        total_transactions,
        avg_order_value,
        ROUND(
            total_revenue * 100.0 / SUM(total_revenue) OVER (PARTITION BY region_name),
            2
        ) AS region_channel_share_pct
    FROM channel_summary
    ORDER BY region_name, total_revenue DESC;
    """

    df_regional = run_query(query_regional_channel)

    col1, col2 = st.columns([3, 2])

    with col1:
        fig_channel = px.bar(
            df_regional,
            x="region_name",
            y="total_revenue",
            color="platform_name",
            barmode="group",
            title="Total Revenue by Region and Sales Channel (Multi-Table JOIN)",
            labels={"region_name": "Region", "total_revenue": "Revenue ($)", "platform_name": "Channel"}
        )
        st.plotly_chart(fig_channel, use_container_width=True)

    with col2:
        fig_share = px.bar(
            df_regional,
            x="region_name",
            y="region_channel_share_pct",
            color="platform_name",
            barmode="stack",
            text="region_channel_share_pct",
            title="Channel Revenue Share (%) by Region",
            labels={"region_name": "Region", "region_channel_share_pct": "Share %", "platform_name": "Channel"}
        )
        fig_share.update_traces(texttemplate="%{text}%", textposition="inside")
        st.plotly_chart(fig_share, use_container_width=True)

    st.markdown("#### Regional Channel Summary Table")
    st.dataframe(df_regional, use_container_width=True, hide_index=True)


# ==========================================================
# TAB 2: Demographic Channel Affinity & Basket Size
# ==========================================================
with tab2:
    st.subheader("Demographic Channel Adoption & Basket Size (AOV)")

    query_demographic_channel = """
    SELECT
        p.platform_name,
        s.demographic,
        s.age_band,
        SUM(f.sales) AS total_revenue,
        SUM(f.transactions) AS total_transactions,
        ROUND(SUM(f.sales) / NULLIF(SUM(f.transactions), 0), 2) AS avg_order_value
    FROM fact_weekly_sales f
    INNER JOIN dim_platform p ON f.platform_id = p.platform_id
    INNER JOIN dim_segment s ON f.segment_id = s.segment_id
    WHERE s.segment_code != 'unknown'
    GROUP BY p.platform_name, s.demographic, s.age_band
    ORDER BY p.platform_name, total_revenue DESC;
    """

    df_demo_channel = run_query(query_demographic_channel)

    col1, col2 = st.columns(2)

    with col1:
        fig_demo_rev = px.bar(
            df_demo_channel,
            x="age_band",
            y="total_revenue",
            color="demographic",
            barmode="group",
            facet_col="platform_name",
            title="Demographic Revenue by Platform",
            labels={"age_band": "Age Band", "total_revenue": "Revenue ($)", "demographic": "Demographic"}
        )
        st.plotly_chart(fig_demo_rev, use_container_width=True)

    with col2:
        fig_aov = px.bar(
            df_demo_channel,
            x="age_band",
            y="avg_order_value",
            color="platform_name",
            barmode="group",
            title="Average Order Value (AOV) Comparison ($)",
            labels={"age_band": "Age Band", "avg_order_value": "Avg Order Value ($)", "platform_name": "Channel"}
        )
        st.plotly_chart(fig_aov, use_container_width=True)

    st.markdown("#### Detailed Demographic Purchasing Matrix")
    st.dataframe(df_demo_channel, use_container_width=True, hide_index=True)


# ==========================================================
# TAB 3: Data Management (CRUD)
# ==========================================================
with tab3:
    st.subheader("Interactive Database Data Management (CRUD)")
    st.markdown("Insert new sales records with relational foreign key validation, or delete transactions from `fact_weekly_sales`.")

    action = st.radio("Select Action:", ["➕ Insert New Sales Record", "🗑️ Delete Sales Records"], horizontal=True)

    regions_df = run_query("SELECT region_id, region_name FROM dim_region ORDER BY region_name;")
    platforms_df = run_query("SELECT platform_id, platform_name FROM dim_platform ORDER BY platform_name;")
    segments_df = run_query("SELECT segment_id, segment_code, demographic, age_band FROM dim_segment ORDER BY segment_code;")

    if action == "➕ Insert New Sales Record":
        with st.form("add_sales_record_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                input_date = st.date_input("Week Date", value=datetime.today())
                selected_region_name = st.selectbox("Region", regions_df["region_name"])
            
            with col2:
                selected_platform_name = st.selectbox("Platform", platforms_df["platform_name"])
                selected_segment_code = st.selectbox("Customer Segment", segments_df["segment_code"])

            with col3:
                customer_type = st.selectbox("Customer Type", ["New", "Existing", "Guest"])
                transactions = st.number_input("Total Transactions", min_value=1, value=100, step=1)
                sales = st.number_input("Total Sales Amount ($)", min_value=1.0, value=5000.0, step=100.0)

            submit_btn = st.form_submit_button("✅ Insert Record into Database")

            if submit_btn:
                try:
                    reg_id = int(regions_df[regions_df["region_name"] == selected_region_name]["region_id"].iloc[0])
                    plat_id = int(platforms_df[platforms_df["platform_name"] == selected_platform_name]["platform_id"].iloc[0])
                    seg_id = int(segments_df[segments_df["segment_code"] == selected_segment_code]["segment_id"].iloc[0])
                    
                    week_str = input_date.strftime("%Y-%m-%d")
                    week_num = int(input_date.strftime("%W")) + 1
                    month_num = input_date.month
                    year_num = input_date.year
                    avg_tx = round(sales / transactions, 2)

                    insert_sql = """
                    INSERT INTO fact_weekly_sales (
                        week_date, week_number, month_number, calendar_year,
                        region_id, platform_id, segment_id,
                        customer_type, transactions, sales, avg_transaction
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    execute_non_query(insert_sql, (
                        week_str, week_num, month_num, year_num,
                        reg_id, plat_id, seg_id,
                        customer_type, int(transactions), float(sales), float(avg_tx)
                    ))
                    st.success(f"🎉 Successfully inserted sales record for {selected_region_name} ({selected_platform_name})!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error inserting record: {str(e)}")

    elif action == "🗑️ Delete Sales Records":
        st.write("Recent records in `fact_weekly_sales` (select checkboxes to delete):")
        recent_records = run_query("""
        SELECT 
            f.sales_id,
            f.week_date,
            r.region_name,
            p.platform_name,
            s.segment_code,
            f.customer_type,
            f.transactions,
            f.sales
        FROM fact_weekly_sales f
        JOIN dim_region r ON f.region_id = r.region_id
        JOIN dim_platform p ON f.platform_id = p.platform_id
        JOIN dim_segment s ON f.segment_id = s.segment_id
        ORDER BY f.sales_id DESC
        LIMIT 50;
        """)

        if not recent_records.empty:
            recent_records.insert(0, "Select", False)
            edited_df = st.data_editor(
                recent_records,
                column_config={"Select": st.column_config.CheckboxColumn("Select")},
                disabled=[col for col in recent_records.columns if col != "Select"],
                hide_index=True,
                use_container_width=True
            )

            if st.button("🗑️ Delete Selected Record(s)"):
                selected_ids = edited_df[edited_df["Select"] == True]["sales_id"].tolist()
                if selected_ids:
                    try:
                        for s_id in selected_ids:
                            execute_non_query("DELETE FROM fact_weekly_sales WHERE sales_id = %s;", (int(s_id),))
                        st.success(f"✅ Successfully deleted {len(selected_ids)} record(s) from database!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting record: {str(e)}")
                else:
                    st.warning("Please check at least one box to delete.")
        else:
            st.info("No records found in database.")
