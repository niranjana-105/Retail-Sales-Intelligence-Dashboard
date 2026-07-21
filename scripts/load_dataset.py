import pandas as pd
import mysql.connector

# ----------------------------
# MySQL Connection
# ----------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="chakki2005"   # <-- Change this
)

cursor = conn.cursor()

# ----------------------------
# Create Database
# ----------------------------
cursor.execute("CREATE DATABASE IF NOT EXISTS data_mart")
cursor.execute("USE data_mart")

# ----------------------------
# Create Table
# ----------------------------
cursor.execute("""
DROP TABLE IF EXISTS weekly_sales;
""")

cursor.execute("""
CREATE TABLE weekly_sales (
    week_date VARCHAR(10),
    region VARCHAR(13),
    platform VARCHAR(7),
    segment VARCHAR(4),
    customer_type VARCHAR(8),
    transactions INT,
    sales DECIMAL(14,2)
)
""")

# ----------------------------
# Read CSV
# ----------------------------
df = pd.read_csv("data_mart_weekly_sales_fixed.csv")

# ----------------------------
# Insert Data
# ----------------------------
sql = """
INSERT INTO weekly_sales
(week_date, region, platform, segment, customer_type, transactions, sales)
VALUES (%s,%s,%s,%s,%s,%s,%s)
"""

cursor.executemany(sql, df.values.tolist())

conn.commit()

print(f"Inserted {cursor.rowcount} rows successfully!")

cursor.close()
conn.close()