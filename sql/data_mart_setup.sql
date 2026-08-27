/*
===============================================================================
Data Mart Database Setup & Star Schema Normalization
===============================================================================
This script demonstrates:
1. Raw Data Ingestion
2. Data Cleaning & Feature Engineering
3. Dimensional Modeling / Star Schema Normalization:
   - Dimension: dim_region
   - Dimension: dim_platform
   - Dimension: dim_segment
   - Fact Table: fact_weekly_sales (with Foreign Keys)
4. Unified Analytical View: clean_weekly_sales
===============================================================================
*/

CREATE DATABASE IF NOT EXISTS data_mart;
USE data_mart;

-- ==========================================================
-- 1. Create Dimension: dim_region
-- ==========================================================
DROP TABLE IF EXISTS dim_region;
CREATE TABLE dim_region (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(20) NOT NULL UNIQUE
);

-- ==========================================================
-- 2. Create Dimension: dim_platform
-- ==========================================================
DROP TABLE IF EXISTS dim_platform;
CREATE TABLE dim_platform (
    platform_id INT AUTO_INCREMENT PRIMARY KEY,
    platform_name VARCHAR(15) NOT NULL UNIQUE
);

-- ==========================================================
-- 3. Create Dimension: dim_segment
-- ==========================================================
DROP TABLE IF EXISTS dim_segment;
CREATE TABLE dim_segment (
    segment_id INT AUTO_INCREMENT PRIMARY KEY,
    segment_code VARCHAR(10) NOT NULL UNIQUE,
    age_band VARCHAR(20) NOT NULL,
    demographic VARCHAR(20) NOT NULL
);

-- ==========================================================
-- 4. Create Fact Table: fact_weekly_sales
-- ==========================================================
DROP TABLE IF EXISTS fact_weekly_sales;
CREATE TABLE fact_weekly_sales (
    sales_id INT AUTO_INCREMENT PRIMARY KEY,
    week_date DATE NOT NULL,
    week_number INT NOT NULL,
    month_number INT NOT NULL,
    calendar_year INT NOT NULL,
    region_id INT NOT NULL,
    platform_id INT NOT NULL,
    segment_id INT NOT NULL,
    customer_type VARCHAR(15) NOT NULL,
    transactions INT NOT NULL,
    sales DECIMAL(14,2) NOT NULL,
    avg_transaction DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (region_id) REFERENCES dim_region(region_id),
    FOREIGN KEY (platform_id) REFERENCES dim_platform(platform_id),
    FOREIGN KEY (segment_id) REFERENCES dim_segment(segment_id)
);

-- ==========================================================
-- 5. Populate Dimension Tables from Raw weekly_sales
-- ==========================================================
INSERT INTO dim_region (region_name)
SELECT DISTINCT UPPER(TRIM(region))
FROM weekly_sales
ORDER BY 1;

INSERT INTO dim_platform (platform_name)
SELECT DISTINCT TRIM(platform)
FROM weekly_sales
ORDER BY 1;

INSERT INTO dim_segment (segment_code, age_band, demographic)
SELECT DISTINCT
    COALESCE(NULLIF(TRIM(segment), 'null'), 'unknown') AS segment_code,
    CASE
        WHEN RIGHT(TRIM(segment), 1) = '1' THEN 'Young Adults'
        WHEN RIGHT(TRIM(segment), 1) = '2' THEN 'Middle Aged'
        WHEN RIGHT(TRIM(segment), 1) IN ('3', '4') THEN 'Retirees'
        ELSE 'unknown'
    END AS age_band,
    CASE
        WHEN LEFT(TRIM(segment), 1) = 'C' THEN 'Couples'
        WHEN LEFT(TRIM(segment), 1) = 'F' THEN 'Families'
        ELSE 'unknown'
    END AS demographic
FROM weekly_sales;

-- ==========================================================
-- 6. Populate Fact Table: fact_weekly_sales
-- ==========================================================
INSERT INTO fact_weekly_sales (
    week_date, week_number, month_number, calendar_year,
    region_id, platform_id, segment_id,
    customer_type, transactions, sales, avg_transaction
)
SELECT
    STR_TO_DATE(w.week_date, '%e/%c/%y') AS week_date,
    WEEK(STR_TO_DATE(w.week_date, '%e/%c/%y'), 3) AS week_number,
    MONTH(STR_TO_DATE(w.week_date, '%e/%c/%y')) AS month_number,
    YEAR(STR_TO_DATE(w.week_date, '%e/%c/%y')) AS calendar_year,
    r.region_id,
    p.platform_id,
    s.segment_id,
    w.customer_type,
    w.transactions,
    w.sales,
    ROUND(w.sales / w.transactions, 2) AS avg_transaction
FROM weekly_sales w
JOIN dim_region r ON UPPER(TRIM(w.region)) = r.region_name
JOIN dim_platform p ON TRIM(w.platform) = p.platform_name
JOIN dim_segment s ON COALESCE(NULLIF(TRIM(w.segment), 'null'), 'unknown') = s.segment_code;

-- ==========================================================
-- 7. Unified Analytical View
-- ==========================================================
CREATE OR REPLACE VIEW clean_weekly_sales AS
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

-- ==========================================================
-- 8. Verification Queries
-- ==========================================================
SELECT COUNT(*) AS total_regions FROM dim_region;
SELECT COUNT(*) AS total_platforms FROM dim_platform;
SELECT COUNT(*) AS total_segments FROM dim_segment;
SELECT COUNT(*) AS total_fact_records FROM fact_weekly_sales;
SELECT COUNT(*) AS total_view_records FROM clean_weekly_sales;