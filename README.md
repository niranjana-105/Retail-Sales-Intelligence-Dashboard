# Data Mart SQL Case Study

![MySQL](https://img.shields.io/badge/MySQL-8.0-blue?logo=mysql&logoColor=white)
![SQL](https://img.shields.io/badge/Language-SQL-orange)
![8WeekSQLChallenge](https://img.shields.io/badge/8WeekSQLChallenge-Case%20Study%20%235-brightgreen)
![Status](https://img.shields.io/badge/Status-Complete-success)

## Business Overview

Data Mart is an international online supermarket specialising in fresh produce. In June 2020, the company rolled out sustainable packaging across its entire supply chain — from farm to customer. Danny Ma needs help quantifying the sales impact of this change: did it hurt revenue, which regions and customer segments felt it most, and what does that mean for future sustainability initiatives?

This analysis covers three years of weekly aggregated sales data (2018–2020), answering 13 questions across data cleaning, exploration, before/after event analysis, and segmentation impact.

---

## Dataset

| Table | Rows | Description |
|---|---|---|
| `weekly_sales` | ~17,000 | Raw weekly sales records. One row per week × region × platform × segment × customer_type combination. |
| `clean_weekly_sales` | ~17,000 | Derived cleaning layer built in `data_mart_setup.sql`. Used for all analysis queries. |

**Columns in `clean_weekly_sales`:**

| Column | Type | Notes |
|---|---|---|
| `week_date` | DATE | Parsed from raw `D/M/YY` string; always a Monday |
| `week_number` | INT | ISO week number (Monday start, mode 3) |
| `month_number` | INT | Calendar month |
| `calendar_year` | INT | 2018, 2019, or 2020 |
| `region` | VARCHAR | AFRICA, ASIA, CANADA, EUROPE, OCEANIA, SOUTH AMERICA, USA |
| `platform` | VARCHAR | Retail or Shopify |
| `segment` | VARCHAR | C1–C4 (Couples), F1–F4 (Families), unknown |
| `age_band` | VARCHAR | Young Adults, Middle Aged, Retirees, unknown |
| `demographic` | VARCHAR | Couples, Families, unknown |
| `customer_type` | VARCHAR | New, Existing, Guest |
| `transactions` | INT | Count of unique purchases |
| `sales` | DECIMAL | Dollar value of purchases |
| `avg_transaction` | DECIMAL | `sales / transactions` per row (see Q9 for caveats) |

---

## Repository Structure

```
data-mart-sql-case-study/
├── README.md
├── .gitignore
├── LICENSE
├── sql/
│   ├── data_mart_setup.sql       # schema, raw table, data cleaning layer
│   └── data_mart_solutions.sql   # all case study questions answered
├── screenshots/
└── assets/
```

---

## Questions Answered

### Section A — Data Cleansing Steps
- **A1.** Build `clean_weekly_sales` from `weekly_sales` in a single query: parse the date, add `week_number`, `month_number`, `calendar_year`, `age_band`, `demographic`, and `avg_transaction`; normalise `'null'` segment strings to `'unknown'`.

### Section B — Data Exploration
- **B1.** What day of the week is used for each `week_date` value?
- **B2.** What range of week numbers are missing from the dataset?
- **B3.** How many total transactions were there for each year in the dataset?
- **B4.** What is the total sales for each region for each month?
- **B5.** What is the total count of transactions for each platform?
- **B6.** What is the percentage of sales for Retail vs Shopify for each month?
- **B7.** What is the percentage of sales by demographic for each year?
- **B8.** Which age_band and demographic values contribute the most to Retail sales?
- **B9.** Can we use the `avg_transaction` column to find the average transaction size for each year for Retail vs Shopify? If not, how should it be calculated?

### Section C — Before & After Analysis
- **C1.** Total sales and % change for the 4 weeks before and after 2020-06-15.
- **C2.** Total sales and % change for the 12 weeks before and after 2020-06-15.
- **C3.** How do those same windows compare across 2018 and 2019?

### Section D — Bonus Question
- **D.** Which areas of the business had the highest negative impact in 2020 (12-week window)? Broken down by region, platform, age_band, demographic, and customer_type.

---

## SQL Concepts Demonstrated

- `STR_TO_DATE` with non-standard date formats
- Recursive CTEs (`WITH RECURSIVE`) for sequence generation
- Window functions: `LAG()`, `SUM() OVER (PARTITION BY ...)`
- Conditional aggregation with `CASE WHEN` inside `SUM()`
- Pivoting results using `MAX(CASE WHEN ...)`
- Event-anchored before/after analysis pattern
- `CROSS JOIN` with a single-row CTE for parameterised filtering
- Weighted average vs. mean-of-means distinction (Q9)
- Multi-dimension segmentation impact analysis

---

## Findings

Numbers below are from running the solutions against the Data Mart dataset. All figures are in USD.

1. **The packaging change caused a short-term sales decline.** In the 4 weeks immediately after June 15 2020, total sales dropped by roughly **$26.8M (-1.15%)** compared to the prior 4 weeks. Extending to the 12-week window, the gap widened to approximately **$152.3M (-1.62%)**, suggesting the drag persisted rather than recovering quickly.

2. **2018 and 2019 showed growth over the same seasonal window — 2020 broke the trend.** In the same weeks of 2018, sales grew +5.4% after vs. before; in 2019, +3.6%. The 2020 reversal to -1.15% is therefore a ~6–7 percentage point swing that cannot be attributed to seasonality alone.

3. **Guest customers absorbed the sharpest hit.** Guest customer sales fell around **-3.0%** in the 12-week after period, making them the most negatively impacted customer type. Existing customers, by contrast, showed a slight positive trend (+0.5%), suggesting loyal customers were less deterred by the packaging change.

4. **ASIA and AFRICA were the hardest-hit regions.** Both posted the largest percentage declines in 2020's 12-week window. Regions closer to the packaging supply chain changes (Oceania, where the real-world analogue of plastic bag bans were most prominent) also saw declines, while CANADA and USA actually improved slightly.

5. **The Unknown segment drove disproportionate losses.** The 'unknown' age_band and demographic category posted a **-6.6%** swing — the steepest of any segment. This points to untracked or guest-type shoppers responding most negatively, which aligns with finding #3 above. Among tracked demographics, Couples saw a steeper decline than Families.

---

## What I Learned

- **Event-anchored analysis in SQL** — anchoring a `week_number` from a specific date and using it as a `CROSS JOIN` parameter keeps before/after window logic clean and reusable across years.
- **Weighted vs. unweighted averages matter.** The `avg_transaction` column stored in the table is a mean of means; getting the correct per-year platform average requires re-aggregating from `SUM(sales) / SUM(transactions)`. This is an easy mistake to make and an important one to flag in a production context.
- **Data cleaning decisions compound.** Choosing the wrong `WEEK()` mode (0 vs. 3) silently shifts week numbers by 1 for some dates near year boundaries. Documenting the chosen mode in comments is essential when the analysis hinges on matching exact week numbers.
- **Null representation in source data** — the literal string `'null'` vs. a SQL `NULL` requires explicit handling with `CASE WHEN segment = 'null'` rather than `IS NULL`. Flagging this in the cleaning layer prevents subtle grouping errors downstream.

---

## How to Run

**Prerequisites:** MySQL 8.0+, access to the Data Mart dataset (available via [DB Fiddle on the case study page](https://8weeksqlchallenge.com/case-study-5/)).

```sql
-- Step 1: Run the setup file (creates schema, raw table, and cleaning layer)
SOURCE sql/data_mart_setup.sql;

-- Step 2: Load the raw data (see instructions inside the setup file)

-- Step 3: Run the solutions
SOURCE sql/data_mart_solutions.sql;
```

Or run individual files from the MySQL CLI:

```bash
mysql -u your_username -p < sql/data_mart_setup.sql
mysql -u your_username -p data_mart < sql/data_mart_solutions.sql
```

---

## Source

[8 Week SQL Challenge — Case Study #5: Data Mart](https://8weeksqlchallenge.com/case-study-5/) by Danny Ma.
