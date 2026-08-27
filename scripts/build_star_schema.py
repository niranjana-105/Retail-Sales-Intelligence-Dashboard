import os
import re
import sqlite3
import pandas as pd
from datetime import datetime

DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_FILE = os.path.join(DATA_DIR, "sql", "dataset_mysql.sql")
CSV_FILE = os.path.join(DATA_DIR, "scripts", "weekly_sales.csv")
DB_FILE = os.path.join(DATA_DIR, "data_mart.db")


def extract_raw_records_from_sql(sql_path):
    """Extract raw tuples from INSERT statements in dataset_mysql.sql"""
    records = []
    # Pattern to match: ('31/8/20', 'ASIA', 'Retail', 'C3', 'New', '120631', '3656163')
    tuple_pattern = re.compile(
        r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)"
    )

    with open(sql_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("(") and ("Retail" in line or "Shopify" in line):
                matches = tuple_pattern.findall(line)
                for match in matches:
                    week_date, region, platform, segment, customer_type, transactions, sales = match
                    records.append({
                        "week_date": week_date,
                        "region": region.upper(),
                        "platform": platform,
                        "segment": segment,
                        "customer_type": customer_type,
                        "transactions": int(transactions),
                        "sales": float(sales)
                    })
    return pd.DataFrame(records)


def build_star_schema(conn=None, db_path=DB_FILE):
    """Builds and populates the 4-Table Star Schema (dim_region, dim_platform, dim_segment, fact_weekly_sales)"""
    if conn is None:
        conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    # 1. Load Raw Data
    if os.path.exists(CSV_FILE):
        raw_df = pd.read_csv(CSV_FILE)
    elif os.path.exists(SQL_FILE):
        raw_df = extract_raw_records_from_sql(SQL_FILE)
        raw_df.to_csv(CSV_FILE, index=False)
    else:
        raise FileNotFoundError("Neither weekly_sales.csv nor dataset_mysql.sql found.")

    # 2. Clean and Engineer Columns
    cleaned_rows = []
    for _, row in raw_df.iterrows():
        # Parse date
        raw_date_str = str(row["week_date"]).strip()
        try:
            dt = datetime.strptime(raw_date_str, "%d/%m/%y")
        except ValueError:
            try:
                dt = datetime.strptime(raw_date_str, "%Y-%m-%d")
            except ValueError:
                dt = datetime.strptime(raw_date_str, "%d/%m/%Y")

        clean_date = dt.strftime("%Y-%m-%d")
        week_number = int(dt.strftime("%W")) + 1
        month_number = dt.month
        calendar_year = dt.year

        # Segment / Demographic / Age Band
        raw_segment = str(row["segment"]).strip()
        if raw_segment.lower() in ("null", "none", "", "nan"):
            segment_code = "unknown"
            demographic = "unknown"
            age_band = "unknown"
        else:
            segment_code = raw_segment.upper()
            # Demographic
            if segment_code.startswith("C"):
                demographic = "Couples"
            elif segment_code.startswith("F"):
                demographic = "Families"
            else:
                demographic = "unknown"

            # Age band
            if segment_code.endswith("1"):
                age_band = "Young Adults"
            elif segment_code.endswith("2"):
                age_band = "Middle Aged"
            elif segment_code.endswith("3") or segment_code.endswith("4"):
                age_band = "Retirees"
            else:
                age_band = "unknown"

        tx = int(row["transactions"])
        sales = float(row["sales"])
        avg_tx = round(sales / tx, 2) if tx > 0 else 0.0

        cleaned_rows.append({
            "week_date": clean_date,
            "week_number": week_number,
            "month_number": month_number,
            "calendar_year": calendar_year,
            "region": str(row["region"]).strip().upper(),
            "platform": str(row["platform"]).strip(),
            "segment_code": segment_code,
            "demographic": demographic,
            "age_band": age_band,
            "customer_type": str(row["customer_type"]).strip(),
            "transactions": tx,
            "sales": sales,
            "avg_transaction": avg_tx
        })

    clean_df = pd.DataFrame(cleaned_rows)

    # 3. Create Tables
    cursor.execute("DROP TABLE IF EXISTS fact_weekly_sales;")
    cursor.execute("DROP TABLE IF EXISTS dim_region;")
    cursor.execute("DROP TABLE IF EXISTS dim_platform;")
    cursor.execute("DROP TABLE IF EXISTS dim_segment;")
    cursor.execute("DROP VIEW IF EXISTS clean_weekly_sales;")

    cursor.execute("""
    CREATE TABLE dim_region (
        region_id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE dim_platform (
        platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_name TEXT UNIQUE NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE dim_segment (
        segment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        segment_code TEXT UNIQUE NOT NULL,
        age_band TEXT NOT NULL,
        demographic TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE fact_weekly_sales (
        sales_id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_date TEXT NOT NULL,
        week_number INTEGER NOT NULL,
        month_number INTEGER NOT NULL,
        calendar_year INTEGER NOT NULL,
        region_id INTEGER NOT NULL,
        platform_id INTEGER NOT NULL,
        segment_id INTEGER NOT NULL,
        customer_type TEXT NOT NULL,
        transactions INTEGER NOT NULL,
        sales REAL NOT NULL,
        avg_transaction REAL NOT NULL,
        FOREIGN KEY (region_id) REFERENCES dim_region (region_id),
        FOREIGN KEY (platform_id) REFERENCES dim_platform (platform_id),
        FOREIGN KEY (segment_id) REFERENCES dim_segment (segment_id)
    );
    """)

    # 4. Populate Dimension Tables
    regions = sorted(clean_df["region"].unique())
    for r in regions:
        cursor.execute("INSERT INTO dim_region (region_name) VALUES (?);", (r,))

    platforms = sorted(clean_df["platform"].unique())
    for p in platforms:
        cursor.execute("INSERT INTO dim_platform (platform_name) VALUES (?);", (p,))

    segments_df = clean_df[["segment_code", "age_band", "demographic"]].drop_duplicates()
    for _, row in segments_df.iterrows():
        cursor.execute(
            "INSERT INTO dim_segment (segment_code, age_band, demographic) VALUES (?, ?, ?);",
            (row["segment_code"], row["age_band"], row["demographic"])
        )

    conn.commit()

    # Build lookup dictionaries for foreign key mapping
    region_map = dict(cursor.execute("SELECT region_name, region_id FROM dim_region;").fetchall())
    platform_map = dict(cursor.execute("SELECT platform_name, platform_id FROM dim_platform;").fetchall())
    segment_map = dict(cursor.execute("SELECT segment_code, segment_id FROM dim_segment;").fetchall())

    # 5. Populate Fact Table
    fact_records = []
    for _, row in clean_df.iterrows():
        fact_records.append((
            row["week_date"],
            row["week_number"],
            row["month_number"],
            row["calendar_year"],
            region_map[row["region"]],
            platform_map[row["platform"]],
            segment_map[row["segment_code"]],
            row["customer_type"],
            row["transactions"],
            row["sales"],
            row["avg_transaction"]
        ))

    cursor.executemany("""
    INSERT INTO fact_weekly_sales (
        week_date, week_number, month_number, calendar_year,
        region_id, platform_id, segment_id,
        customer_type, transactions, sales, avg_transaction
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, fact_records)

    # 6. Create Analytical View for Backwards Compatibility
    cursor.execute("""
    CREATE VIEW clean_weekly_sales AS
    SELECT
        f.sales_id,
        f.week_date,
        f.week_number,
        f.month_number,
        f.calendar_year,
        r.region_name AS region,
        p.platform_name AS platform,
        s.segment_code AS segment,
        s.age_band,
        s.demographic,
        f.customer_type,
        f.transactions,
        f.sales,
        f.avg_transaction
    FROM fact_weekly_sales f
    JOIN dim_region r ON f.region_id = r.region_id
    JOIN dim_platform p ON f.platform_id = p.platform_id
    JOIN dim_segment s ON f.segment_id = s.segment_id;
    """)

    conn.commit()
    print(f"Star Schema successfully built! Inserted {len(fact_records)} records into fact_weekly_sales.")
    return conn


if __name__ == "__main__":
    build_star_schema()
