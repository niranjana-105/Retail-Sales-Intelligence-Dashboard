# Retail Sales Intelligence Dashboard

An interactive Business Intelligence dashboard built using **MySQL**, **SQL**, **Python**, **Streamlit**, and **Plotly** to analyze retail sales data from the **8 Week SQL Challenge – Data Mart** case study.

The project demonstrates the complete analytics workflow, from data cleaning and SQL-based business analysis to interactive dashboard development.

---

## Features

- ETL pipeline for cleaning and transforming raw sales data
- 25+ business SQL queries covering:
  - Aggregations
  - Common Table Expressions (CTEs)
  - Window Functions
  - Ranking
  - Business KPIs
- Interactive Streamlit dashboard
- Customer segmentation analysis
- Regional sales analysis
- Platform performance (Retail vs Shopify)
- Packaging impact analysis
- Interactive charts using Plotly

---

## Dashboard

### Overview

- KPI Cards
  - Total Sales
  - Total Transactions
  - Average Transaction
  - Regions Covered
- Monthly Sales Trend
- Sales by Region
- Platform Distribution

### Sales Analysis

- Monthly Sales
- Regional Performance
- Platform Comparison
- Top Performing Regions

### Customer Analysis

- Sales by Demographic
- Sales by Age Band
- Customer Type Analysis
- Customer Segment Summary

### Business Insights

- Packaging Change Impact
- Top Revenue Regions
- Highest Revenue Customer Segments
- Annual Sales Trend

---

## Project Structure

```
Retail-Sales-Intelligence-Dashboard/
│
├── app.py
├── db.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Sales_Analysis.py
│   ├── 3_Customer_Analysis.py
│   └── 4_Business_Insights.py
│
├── sql/
│   ├── dataset_mysql.sql
│   ├── data_mart_setup.sql
│   ├── data_mart_solutions.sql
│   └── advanced_business_insights.sql
│
└── scripts/
    └── load_dataset.py
```

---

## Technologies Used

- MySQL
- SQL
- Python
- Streamlit
- Plotly
- Pandas
- Git

---

## SQL Concepts Demonstrated

- Data Cleaning
- Feature Engineering
- Aggregate Functions
- GROUP BY
- CASE Statements
- Common Table Expressions (CTEs)
- Window Functions
- LAG()
- RANK()
- DENSE_RANK()
- Running Totals
- Percentage Contribution Analysis
- Business KPI Calculations

---

## Dataset

This project uses the **Data Mart** case study from the **8 Week SQL Challenge** by Danny Ma.

The dataset contains weekly retail sales information including:

- Sales
- Transactions
- Regions
- Customer Demographics
- Customer Segments
- Retail & Shopify Platforms

---

## Installation

Clone the repository

```bash
git clone https://github.com/<your_username>/Retail-Sales-Intelligence-Dashboard.git
```

Move into the project

```bash
cd Retail-Sales-Intelligence-Dashboard
```

Install dependencies

```bash
pip install -r requirements.txt
```

Configure MySQL credentials inside **db.py**

Run the Streamlit application

```bash
streamlit run app.py
```

---

## Screenshots

### Overview Dashboard

_Add screenshot here_

### Sales Analysis

_Add screenshot here_

### Customer Analysis

_Add screenshot here_

### Business Insights

_Add screenshot here_

---

## Future Improvements

- Global dashboard filters
- Additional business KPIs
- Forecasting using Machine Learning
- Dashboard deployment
- User authentication

