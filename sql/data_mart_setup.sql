USE data_mart;

DROP TABLE IF EXISTS clean_weekly_sales;

CREATE TABLE clean_weekly_sales AS

SELECT
    week_date,
    WEEK(week_date,3) AS week_number,
    MONTH(week_date) AS month_number,
    YEAR(week_date) AS calendar_year,
    region,
    platform,
    segment,

    CASE
        WHEN RIGHT(segment,1)='1' THEN 'Young Adults'
        WHEN RIGHT(segment,1)='2' THEN 'Middle Aged'
        WHEN RIGHT(segment,1) IN ('3','4') THEN 'Retirees'
        ELSE 'unknown'
    END AS age_band,

    CASE
        WHEN LEFT(segment,1)='C' THEN 'Couples'
        WHEN LEFT(segment,1)='F' THEN 'Families'
        ELSE 'unknown'
    END AS demographic,

    customer_type,
    transactions,
    sales,
    ROUND(sales/transactions,2) AS avg_transaction

FROM (

        SELECT
        STR_TO_DATE(week_date,'%e/%c/%y') AS week_date,
        region,
        platform,
        COALESCE(NULLIF(segment,'null'),'unknown') AS segment,
        customer_type,
        transactions,
        sales
    FROM weekly_sales

) x;

-- ==========================================================
-- Verification
-- ==========================================================

SELECT COUNT(*) AS raw_rows
FROM weekly_sales;

SELECT COUNT(*) AS cleaned_rows
FROM clean_weekly_sales;

SELECT DISTINCT DAYNAME(week_date)
FROM clean_weekly_sales;

SELECT DISTINCT segment
FROM clean_weekly_sales;

SELECT MIN(week_date), MAX(week_date)
FROM clean_weekly_sales;