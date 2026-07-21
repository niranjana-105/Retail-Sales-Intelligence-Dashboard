/*
===============================================================================
Advanced Business Insights
Author: Niranjana Nitin

Description:
Additional SQL analyses built on top of the original
8 Week SQL Challenge - Data Mart dataset.

These queries demonstrate:
- Common Table Expressions (CTEs)
- Window Functions
- Ranking
- Running Totals
- Growth Analysis
- Business KPI calculations
===============================================================================
*/

USE data_mart;

-- ============================================================================
-- Query 1: Year-over-Year Sales Growth by Region
-- Purpose:
-- Shows how sales have grown (or declined) for every region compared
-- to the previous year using the LAG() window function.
-- ============================================================================

WITH yearly_sales AS (
    SELECT
        region,
        calendar_year,
        SUM(sales) AS total_sales
    FROM clean_weekly_sales
    GROUP BY region, calendar_year
)

SELECT
    region,
    calendar_year,
    total_sales,
    LAG(total_sales)
        OVER(PARTITION BY region ORDER BY calendar_year)
        AS previous_year_sales,

    ROUND(
        (
            total_sales -
            LAG(total_sales)
            OVER(PARTITION BY region ORDER BY calendar_year)
        ) * 100.0 /

        LAG(total_sales)
        OVER(PARTITION BY region ORDER BY calendar_year),
    2) AS growth_percentage

FROM yearly_sales
ORDER BY region, calendar_year;



-- ============================================================================
-- Query 2: Top Revenue Generating Region Every Year
-- Purpose:
-- Finds the highest revenue region for each year using RANK().
-- ============================================================================

WITH region_sales AS (

SELECT
    calendar_year,
    region,
    SUM(sales) AS total_sales,

    RANK() OVER(
        PARTITION BY calendar_year
        ORDER BY SUM(sales) DESC
    ) AS sales_rank

FROM clean_weekly_sales

GROUP BY
    calendar_year,
    region

)

SELECT *
FROM region_sales
WHERE sales_rank = 1;



-- ============================================================================
-- Query 3: Regions with Highest Average Transaction Value
-- Purpose:
-- Determines which regions generate the highest average transaction.
-- ============================================================================

SELECT

    region,

    ROUND(
        AVG(avg_transaction),
        2
    ) AS average_transaction_value

FROM clean_weekly_sales

GROUP BY region

ORDER BY average_transaction_value DESC;



-- ============================================================================
-- Query 4: Monthly Running Sales Total
-- Purpose:
-- Calculates cumulative sales month-by-month for every year.
-- Demonstrates Running Total using Window Functions.
-- ============================================================================

SELECT

    calendar_year,

    month_number,

    SUM(sales) AS monthly_sales,

    SUM(SUM(sales))
    OVER(
        PARTITION BY calendar_year
        ORDER BY month_number
    ) AS running_total_sales

FROM clean_weekly_sales

GROUP BY
    calendar_year,
    month_number

ORDER BY
    calendar_year,
    month_number;



-- ============================================================================
-- Query 5: Contribution of Each Region to Overall Revenue
-- Purpose:
-- Calculates the percentage contribution of every region
-- to total company sales.
-- ============================================================================

SELECT

    region,

    ROUND(
        SUM(sales),
        2
    ) AS total_sales,

    ROUND(

        SUM(sales) * 100 /

        (
            SELECT SUM(sales)
            FROM clean_weekly_sales
        ),

        2

    ) AS contribution_percentage

FROM clean_weekly_sales

GROUP BY region

ORDER BY contribution_percentage DESC;



-- ============================================================================
-- Query 6: Best Performing Customer Segment
-- Purpose:
-- Identifies which Age Band and Demographic combination
-- contributes the highest revenue.
-- ============================================================================

SELECT

    demographic,

    age_band,

    SUM(sales) AS total_sales,

    SUM(transactions) AS total_transactions

FROM clean_weekly_sales

GROUP BY

    demographic,
    age_band

ORDER BY total_sales DESC;



-- ============================================================================
-- Query 7: Month-over-Month Sales Growth
-- Purpose:
-- Measures monthly growth using LAG().
-- Useful KPI for dashboards.
-- ============================================================================

WITH monthly_sales AS (

SELECT

    calendar_year,

    month_number,

    SUM(sales) AS sales

FROM clean_weekly_sales

GROUP BY
    calendar_year,
    month_number

)

SELECT

    calendar_year,

    month_number,

    sales,

    LAG(sales)
        OVER(
            ORDER BY
            calendar_year,
            month_number
        ) AS previous_month_sales,

    ROUND(

        (

            sales -

            LAG(sales)
            OVER(
                ORDER BY
                calendar_year,
                month_number
            )

        )

        *100/

        LAG(sales)
        OVER(
            ORDER BY
            calendar_year,
            month_number
        ),

        2

    ) AS growth_percentage

FROM monthly_sales;



-- ============================================================================
-- Query 8: Platform Sales Ranking
-- Purpose:
-- Ranks platforms based on total sales using DENSE_RANK().
-- ============================================================================

SELECT

    platform,

    SUM(sales) AS total_sales,

    DENSE_RANK()

    OVER(

        ORDER BY SUM(sales) DESC

    ) AS platform_rank

FROM clean_weekly_sales

GROUP BY platform;



-- ============================================================================
-- Query 9: Top 5 Regions by Revenue
-- Purpose:
-- Displays the five highest revenue generating regions.
-- ============================================================================

SELECT

    region,

    SUM(sales) AS total_sales

FROM clean_weekly_sales

GROUP BY region

ORDER BY total_sales DESC

LIMIT 5;



-- ============================================================================
-- Query 10: Customer Type Performance
-- Purpose:
-- Compares revenue generated by each customer type.
-- Useful for customer segmentation analysis.
-- ============================================================================

SELECT

    customer_type,

    SUM(sales) AS total_sales,

    SUM(transactions) AS total_transactions,

    ROUND(
        AVG(avg_transaction),
        2
    ) AS average_transaction

FROM clean_weekly_sales

GROUP BY customer_type

ORDER BY total_sales DESC;