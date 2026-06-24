-- =============================================================================
-- Case Study #5 - Data Mart
-- Source: https://8weeksqlchallenge.com/case-study-5/
-- Author: raugan
-- Description: Database setup, raw table creation, and data cleaning layer.
--              Run this file first before data_mart_solutions.sql.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. SCHEMA AND RAW TABLE
-- -----------------------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS data_mart;
USE data_mart;

DROP TABLE IF EXISTS weekly_sales;

CREATE TABLE weekly_sales (
    week_date     VARCHAR(7),    -- raw format: D/M/YY (e.g. '9/9/20', '29/7/20')
    region        VARCHAR(13),
    platform      VARCHAR(7),
    segment       VARCHAR(4),    -- values: C1, C2, C3, C4, F1, F2, F3, F4, or literal 'null'
    customer_type VARCHAR(8),
    transactions  INTEGER,
    sales         DECIMAL(14, 2)
);

-- NOTE: The canonical dataset is distributed via DB Fiddle (embedded on the
-- case study page). Load it using one of these methods:
--
--   Option A (recommended): Export the INSERT statements from DB Fiddle and
--   paste them below this comment block.
--
--   Option B: If you have the CSV file (data_mart_weekly_sales.csv), load it:
--
--     LOAD DATA INFILE '/path/to/data_mart_weekly_sales.csv'
--     INTO TABLE weekly_sales
--     FIELDS TERMINATED BY ','
--     OPTIONALLY ENCLOSED BY '"'
--     LINES TERMINATED BY '\n'
--     IGNORE 1 ROWS
--     (week_date, region, platform, segment, customer_type, transactions, sales);

-- <<< PASTE YOUR INSERT STATEMENTS HERE IF USING OPTION A >>>


-- -----------------------------------------------------------------------------
-- 2. DATA CLEANING LAYER
--    Transforms weekly_sales into clean_weekly_sales in a single query.
--
--    Known data quality issues addressed:
--      - week_date is stored as a non-standard VARCHAR ('D/M/YY') rather than
--        a proper DATE column. Converted with STR_TO_DATE.
--      - The segment column uses the literal string 'null' (not a SQL NULL)
--        to represent unknown segments. This is normalised to 'unknown' here
--        and flagged in the derived age_band and demographic columns too.
--      - week_number uses MySQL's WEEK() with mode 3 (ISO-style, weeks start
--        Monday). Mode 0 (default, Sunday start) would produce wrong results
--        given that all week_date values fall on Mondays.
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS clean_weekly_sales;

CREATE TABLE clean_weekly_sales AS
SELECT
    -- Convert D/M/YY string to a proper DATE
    STR_TO_DATE(week_date, '%e/%c/%y')                            AS week_date,

    -- Week number of the year (ISO mode: Monday start, first week = week 1)
    -- WEEK(..., 3) matches the case study's expected week_number definition.
    WEEK(STR_TO_DATE(week_date, '%e/%c/%y'), 3)                   AS week_number,

    MONTH(STR_TO_DATE(week_date, '%e/%c/%y'))                     AS month_number,
    YEAR(STR_TO_DATE(week_date, '%e/%c/%y'))                      AS calendar_year,

    region,
    platform,

    -- Normalise the literal 'null' string to 'unknown'
    CASE WHEN segment = 'null' THEN 'unknown' ELSE segment END    AS segment,

    -- age_band: derived from the numeric part of segment (trailing digit)
    CASE
        WHEN segment = 'null'              THEN 'unknown'
        WHEN RIGHT(segment, 1) = '1'       THEN 'Young Adults'
        WHEN RIGHT(segment, 1) = '2'       THEN 'Middle Aged'
        WHEN RIGHT(segment, 1) IN ('3','4') THEN 'Retirees'
        ELSE 'unknown'
    END                                                           AS age_band,

    -- demographic: derived from the letter prefix of segment
    CASE
        WHEN segment = 'null'              THEN 'unknown'
        WHEN LEFT(segment, 1) = 'C'        THEN 'Couples'
        WHEN LEFT(segment, 1) = 'F'        THEN 'Families'
        ELSE 'unknown'
    END                                                           AS demographic,

    customer_type,
    transactions,
    sales,

    -- avg_transaction: per-row average, NOT the correct way to find period
    -- averages (see Q9 in solutions for explanation). Stored as requested.
    ROUND(sales / transactions, 2)                                AS avg_transaction

FROM weekly_sales;


-- -----------------------------------------------------------------------------
-- 3. VERIFY THE CLEANING LAYER
-- -----------------------------------------------------------------------------

-- Quick sanity checks after loading:
--   SELECT COUNT(*) FROM clean_weekly_sales;           -- should match weekly_sales row count
--   SELECT DISTINCT DAYNAME(week_date) FROM clean_weekly_sales;  -- should return only 'Monday'
--   SELECT DISTINCT segment FROM clean_weekly_sales;   -- no 'null' literals should appear
--   SELECT MIN(week_date), MAX(week_date) FROM clean_weekly_sales;  -- 2018 to 2020
