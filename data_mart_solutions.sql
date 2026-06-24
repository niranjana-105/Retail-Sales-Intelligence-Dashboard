-- =============================================================================
-- Case Study #5 - Data Mart | Solutions
-- Source: https://8weeksqlchallenge.com/case-study-5/
-- Author: raugan
-- Description: All case study questions answered, grouped by section.
--              Run data_mart_setup.sql first to create clean_weekly_sales.
-- =============================================================================

USE data_mart;

-- =============================================================================
-- SECTION A: DATA CLEANSING STEPS
-- =============================================================================
-- The cleaning transformation is handled in data_mart_setup.sql.
-- clean_weekly_sales is the canonical table for all queries below.
-- Refer to that file for documented decisions on NULL handling, date parsing,
-- and week_number mode selection.
-- =============================================================================


-- =============================================================================
-- SECTION B: DATA EXPLORATION
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Question B1: What day of the week is used for each week_date value?
-- -----------------------------------------------------------------------------
SELECT DISTINCT
    DAYNAME(week_date) AS day_of_week
FROM clean_weekly_sales;

-- Expected result: Monday
-- All records represent the start of a sales week, which is consistently Monday.


-- -----------------------------------------------------------------------------
-- Question B2: What range of week numbers are missing from the dataset?
-- -----------------------------------------------------------------------------

-- Generate a complete sequence of week numbers 1-52, then find gaps.
-- Using a recursive CTE to avoid dependency on a numbers table.
WITH RECURSIVE week_sequence (week_num) AS (
    SELECT 1
    UNION ALL
    SELECT week_num + 1
    FROM week_sequence
    WHERE week_num < 52
)
SELECT
    ws.week_num AS missing_week_number
FROM week_sequence AS ws
WHERE ws.week_num NOT IN (
    SELECT DISTINCT week_number
    FROM clean_weekly_sales
)
ORDER BY ws.week_num;

-- NOTE: The dataset covers roughly week 13 to week 36 across all three years,
-- so weeks at the start and end of the calendar year are absent.


-- -----------------------------------------------------------------------------
-- Question B3: How many total transactions were there for each year?
-- -----------------------------------------------------------------------------
SELECT
    calendar_year,
    SUM(transactions) AS total_transactions
FROM clean_weekly_sales
GROUP BY calendar_year
ORDER BY calendar_year;


-- -----------------------------------------------------------------------------
-- Question B4: What is the total sales for each region for each month?
-- -----------------------------------------------------------------------------
SELECT
    region,
    month_number,
    SUM(sales) AS total_sales
FROM clean_weekly_sales
GROUP BY region, month_number
ORDER BY region, month_number;


-- -----------------------------------------------------------------------------
-- Question B5: What is the total count of transactions for each platform?
-- -----------------------------------------------------------------------------
SELECT
    platform,
    SUM(transactions) AS total_transactions
FROM clean_weekly_sales
GROUP BY platform
ORDER BY total_transactions DESC;


-- -----------------------------------------------------------------------------
-- Question B6: What is the percentage of sales for Retail vs Shopify
--              for each month?
-- -----------------------------------------------------------------------------
SELECT
    calendar_year,
    month_number,
    ROUND(
        100.0 * SUM(CASE WHEN platform = 'Retail'  THEN sales END) / SUM(sales),
        2
    ) AS retail_pct,
    ROUND(
        100.0 * SUM(CASE WHEN platform = 'Shopify' THEN sales END) / SUM(sales),
        2
    ) AS shopify_pct
FROM clean_weekly_sales
GROUP BY calendar_year, month_number
ORDER BY calendar_year, month_number;


-- -----------------------------------------------------------------------------
-- Question B7: What is the percentage of sales by demographic for each year?
-- -----------------------------------------------------------------------------
SELECT
    calendar_year,
    demographic,
    ROUND(
        100.0 * SUM(sales) / SUM(SUM(sales)) OVER (PARTITION BY calendar_year),
        2
    ) AS pct_of_annual_sales
FROM clean_weekly_sales
GROUP BY calendar_year, demographic
ORDER BY calendar_year, demographic;


-- -----------------------------------------------------------------------------
-- Question B8: Which age_band and demographic values contribute the most
--              to Retail sales?
-- -----------------------------------------------------------------------------
SELECT
    age_band,
    demographic,
    SUM(sales)                                             AS retail_sales,
    ROUND(100.0 * SUM(sales) / SUM(SUM(sales)) OVER (), 2) AS pct_of_retail_sales
FROM clean_weekly_sales
WHERE platform = 'Retail'
GROUP BY age_band, demographic
ORDER BY retail_sales DESC;


-- -----------------------------------------------------------------------------
-- Question B9: Can we use the avg_transaction column to find the average
--              transaction size for each year for Retail vs Shopify?
--              If not — how would you calculate it instead?
-- -----------------------------------------------------------------------------

-- The avg_transaction column stores a per-row average (sales / transactions
-- for that individual row). Averaging it would produce a mean of means, which
-- gives incorrect results when group sizes differ. The correct approach is to
-- re-aggregate from the raw totals:

SELECT
    calendar_year,
    platform,
    -- WRONG approach (for illustration only — do not use for reporting):
    ROUND(AVG(avg_transaction), 2)            AS incorrect_avg_of_avgs,
    -- CORRECT approach: sum both numerator and denominator first:
    ROUND(SUM(sales) / SUM(transactions), 2)  AS correct_avg_transaction
FROM clean_weekly_sales
GROUP BY calendar_year, platform
ORDER BY calendar_year, platform;


-- =============================================================================
-- SECTION C: BEFORE & AFTER ANALYSIS
-- =============================================================================
-- Baseline: 2020-06-15 is when sustainable packaging changes took effect.
-- "Before" = weeks prior to week 25 (the week containing 2020-06-15).
-- "After"  = week 25 onward.
-- The week_number for 2020-06-15 is 25 (verified: SELECT WEEK('2020-06-15', 3)).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Question C1: What is the total sales for the 4 weeks before and after
--              2020-06-15? What is the growth or reduction rate?
-- -----------------------------------------------------------------------------

-- We anchor on the week_number of the change date to make this robust
-- regardless of the date stored in the table.
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_totals AS (
    SELECT
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 4
                                     AND cw.change_week_num - 1 THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 3 THEN 'after'
        END                   AS period,
        SUM(cws.sales)        AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 4
                              AND cw.change_week_num + 3
    GROUP BY period
    HAVING period IS NOT NULL
)
SELECT
    period,
    total_sales,
    total_sales
        - LAG(total_sales) OVER (ORDER BY period DESC)             AS sales_change,
    ROUND(
        100.0 * (total_sales - LAG(total_sales) OVER (ORDER BY period DESC))
        / LAG(total_sales) OVER (ORDER BY period DESC),
        2
    )                                                              AS pct_change
FROM period_totals
ORDER BY period DESC;


-- -----------------------------------------------------------------------------
-- Question C2: What about the complete 12-week period before and after?
-- -----------------------------------------------------------------------------
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_totals AS (
    SELECT
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END                   AS period,
        SUM(cws.sales)        AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY period
    HAVING period IS NOT NULL
)
SELECT
    period,
    total_sales,
    total_sales
        - LAG(total_sales) OVER (ORDER BY period DESC)             AS sales_change,
    ROUND(
        100.0 * (total_sales - LAG(total_sales) OVER (ORDER BY period DESC))
        / LAG(total_sales) OVER (ORDER BY period DESC),
        2
    )                                                              AS pct_change
FROM period_totals
ORDER BY period DESC;


-- -----------------------------------------------------------------------------
-- Question C3: How do the sale metrics for these 2 periods compare with the
--              previous years in 2018 and 2019?
-- -----------------------------------------------------------------------------
-- Using the same week_number window (±4 weeks around week 25) applied to all
-- three years so the comparison is on the same seasonal window.

-- 4-week window across all years:
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_totals AS (
    SELECT
        cws.calendar_year,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 4
                                     AND cw.change_week_num - 1 THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 3 THEN 'after'
        END                   AS period,
        SUM(cws.sales)        AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.week_number BETWEEN cw.change_week_num - 4
                              AND cw.change_week_num + 3
    GROUP BY cws.calendar_year, period
    HAVING period IS NOT NULL
)
SELECT
    calendar_year,
    period,
    total_sales,
    total_sales
        - LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC) AS sales_change,
    ROUND(
        100.0 * (total_sales - LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC))
        / LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC),
        2
    )                                                                              AS pct_change
FROM period_totals
ORDER BY calendar_year, period DESC;

-- 12-week window across all years:
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_totals AS (
    SELECT
        cws.calendar_year,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END                   AS period,
        SUM(cws.sales)        AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY cws.calendar_year, period
    HAVING period IS NOT NULL
)
SELECT
    calendar_year,
    period,
    total_sales,
    total_sales
        - LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC) AS sales_change,
    ROUND(
        100.0 * (total_sales - LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC))
        / LAG(total_sales) OVER (PARTITION BY calendar_year ORDER BY period DESC),
        2
    )                                                                              AS pct_change
FROM period_totals
ORDER BY calendar_year, period DESC;


-- =============================================================================
-- SECTION D: BONUS QUESTION
-- =============================================================================
-- Which areas of the business have the highest negative impact in 2020
-- for the 12-week before/after period?
-- Broken down by: region, platform, age_band, demographic, customer_type.
-- =============================================================================

-- Helper CTE shared across all five breakdowns. In MySQL you'd repeat it per
-- query; shown once here for readability.

-- D1: By region
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_sales AS (
    SELECT
        region,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END        AS period,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY region, period
    HAVING period IS NOT NULL
)
SELECT
    region,
    MAX(CASE WHEN period = 'before' THEN total_sales END) AS before_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END) AS after_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END)
        - MAX(CASE WHEN period = 'before' THEN total_sales END) AS sales_change,
    ROUND(
        100.0 * (
            MAX(CASE WHEN period = 'after'  THEN total_sales END)
            - MAX(CASE WHEN period = 'before' THEN total_sales END)
        ) / MAX(CASE WHEN period = 'before' THEN total_sales END),
        2
    ) AS pct_change
FROM period_sales
GROUP BY region
ORDER BY pct_change ASC;


-- D2: By platform
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_sales AS (
    SELECT
        platform,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END        AS period,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY platform, period
    HAVING period IS NOT NULL
)
SELECT
    platform,
    MAX(CASE WHEN period = 'before' THEN total_sales END) AS before_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END) AS after_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END)
        - MAX(CASE WHEN period = 'before' THEN total_sales END) AS sales_change,
    ROUND(
        100.0 * (
            MAX(CASE WHEN period = 'after'  THEN total_sales END)
            - MAX(CASE WHEN period = 'before' THEN total_sales END)
        ) / MAX(CASE WHEN period = 'before' THEN total_sales END),
        2
    ) AS pct_change
FROM period_sales
GROUP BY platform
ORDER BY pct_change ASC;


-- D3: By age_band
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_sales AS (
    SELECT
        age_band,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END        AS period,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY age_band, period
    HAVING period IS NOT NULL
)
SELECT
    age_band,
    MAX(CASE WHEN period = 'before' THEN total_sales END) AS before_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END) AS after_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END)
        - MAX(CASE WHEN period = 'before' THEN total_sales END) AS sales_change,
    ROUND(
        100.0 * (
            MAX(CASE WHEN period = 'after'  THEN total_sales END)
            - MAX(CASE WHEN period = 'before' THEN total_sales END)
        ) / MAX(CASE WHEN period = 'before' THEN total_sales END),
        2
    ) AS pct_change
FROM period_sales
GROUP BY age_band
ORDER BY pct_change ASC;


-- D4: By demographic
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_sales AS (
    SELECT
        demographic,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END        AS period,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY demographic, period
    HAVING period IS NOT NULL
)
SELECT
    demographic,
    MAX(CASE WHEN period = 'before' THEN total_sales END) AS before_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END) AS after_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END)
        - MAX(CASE WHEN period = 'before' THEN total_sales END) AS sales_change,
    ROUND(
        100.0 * (
            MAX(CASE WHEN period = 'after'  THEN total_sales END)
            - MAX(CASE WHEN period = 'before' THEN total_sales END)
        ) / MAX(CASE WHEN period = 'before' THEN total_sales END),
        2
    ) AS pct_change
FROM period_sales
GROUP BY demographic
ORDER BY pct_change ASC;


-- D5: By customer_type
WITH change_week AS (
    SELECT DISTINCT week_number AS change_week_num
    FROM clean_weekly_sales
    WHERE week_date = '2020-06-15'
),
period_sales AS (
    SELECT
        customer_type,
        CASE
            WHEN cws.week_number BETWEEN cw.change_week_num - 12
                                     AND cw.change_week_num - 1  THEN 'before'
            WHEN cws.week_number BETWEEN cw.change_week_num
                                     AND cw.change_week_num + 11 THEN 'after'
        END        AS period,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales AS cws
    CROSS JOIN change_week AS cw
    WHERE cws.calendar_year = 2020
      AND cws.week_number BETWEEN cw.change_week_num - 12
                              AND cw.change_week_num + 11
    GROUP BY customer_type, period
    HAVING period IS NOT NULL
)
SELECT
    customer_type,
    MAX(CASE WHEN period = 'before' THEN total_sales END) AS before_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END) AS after_sales,
    MAX(CASE WHEN period = 'after'  THEN total_sales END)
        - MAX(CASE WHEN period = 'before' THEN total_sales END) AS sales_change,
    ROUND(
        100.0 * (
            MAX(CASE WHEN period = 'after'  THEN total_sales END)
            - MAX(CASE WHEN period = 'before' THEN total_sales END)
        ) / MAX(CASE WHEN period = 'before' THEN total_sales END),
        2
    ) AS pct_change
FROM period_sales
GROUP BY customer_type
ORDER BY pct_change ASC;
