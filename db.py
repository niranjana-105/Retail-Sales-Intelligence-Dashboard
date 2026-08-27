import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_mart.db")


def get_connection():
    """Returns a connection to MySQL if configured, or falls back to local SQLite data_mart.db"""
    db_engine = os.getenv("DB_ENGINE", "sqlite").lower()

    if db_engine == "mysql" or os.getenv("DB_PASSWORD"):
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=os.getenv("DB_HOST", "localhost"),
                user=os.getenv("DB_USER", "root"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "data_mart"),
                port=int(os.getenv("DB_PORT", "3306"))
            )
            return conn, "mysql"
        except Exception:
            pass  # Fall back to SQLite if MySQL fails to connect

    # Ensure SQLite DB exists; if not, build it automatically from CSV/SQL
    if not os.path.exists(DB_FILE):
        from scripts.build_star_schema import build_star_schema
        build_star_schema(db_path=DB_FILE)

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    return conn, "sqlite"


def run_query(query, params=None):
    """Executes a SQL query safely across MySQL or SQLite and returns a Pandas DataFrame"""
    conn, engine = get_connection()
    try:
        # SQLite uses '?' placeholder while MySQL uses '%s'
        if engine == "sqlite":
            formatted_query = query.replace("%s", "?")
            # SQLite compatibility for MySQL-specific functions if used
            if params:
                df = pd.read_sql_query(formatted_query, conn, params=list(params) if isinstance(params, (tuple, list)) else [params])
            else:
                df = pd.read_sql_query(formatted_query, conn)
        else:
            df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df


def execute_non_query(statement, params=None):
    """Executes an INSERT, UPDATE, or DELETE statement and commits changes"""
    conn, engine = get_connection()
    try:
        cursor = conn.cursor()
        if engine == "sqlite":
            formatted_statement = statement.replace("%s", "?")
            if params:
                cursor.execute(formatted_statement, tuple(params))
            else:
                cursor.execute(formatted_statement)
        else:
            if params:
                cursor.execute(statement, tuple(params))
            else:
                cursor.execute(statement)
        conn.commit()
        affected_rows = cursor.rowcount
    finally:
        conn.close()
    return affected_rows