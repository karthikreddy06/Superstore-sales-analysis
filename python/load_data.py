"""
Superstore Data Load Script
Loads Sample - Superstore.csv into PostgreSQL database.
Cleans data and parses dates properly (M/D/YYYY format).
"""

import sys
import pandas as pd
from psycopg2.extras import execute_values

from db_config import PROJECT_ROOT, get_connection

CSV_PATH = PROJECT_ROOT / "data" / "Sample - Superstore.csv"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_schema.sql"


def create_table(conn):
    """Create the superstore table using the schema SQL file."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    print("Table created successfully.")


def load_and_clean_data():
    """Load CSV, clean data, parse dates, return DataFrame."""
    print(f"Loading CSV from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, encoding="latin1")
    print(f"Loaded {len(df)} rows.")

    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

    df.columns = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "customer_name", "segment", "country", "city",
        "state", "postal_code", "region", "product_id", "category",
        "sub_category", "product_name", "sales", "quantity", "discount", "profit",
    ]

    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["discount"] = pd.to_numeric(df["discount"], errors="coerce")
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce")
    df["row_id"] = pd.to_numeric(df["row_id"], errors="coerce").astype("Int64")

    df["postal_code"] = df["postal_code"].fillna("").astype(str)

    initial_count = len(df)
    df = df.dropna(subset=["order_id", "order_date", "ship_date", "customer_id"])
    if len(df) < initial_count:
        print(f"Dropped {initial_count - len(df)} rows with missing critical data.")

    print(f"Cleaned data: {len(df)} rows ready for insert.")
    return df


def insert_data(conn, df):
    """Insert DataFrame into PostgreSQL using batch insert."""
    columns = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "customer_name", "segment", "country", "city",
        "state", "postal_code", "region", "product_id", "category",
        "sub_category", "product_name", "sales", "quantity", "discount", "profit",
    ]

    data_tuples = [tuple(row) for row in df[columns].to_numpy()]
    insert_sql = f"INSERT INTO superstore ({', '.join(columns)}) VALUES %s"

    print("Inserting data into database...")
    with conn.cursor() as cur:
        execute_values(cur, insert_sql, data_tuples, page_size=1000)
    conn.commit()
    print(f"Inserted {len(data_tuples)} rows successfully.")


def verify_load(conn):
    """Verify the data was loaded correctly."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM superstore;")
        count = cur.fetchone()[0]
        print(f"Total rows in database: {count}")

        cur.execute("SELECT MIN(order_date), MAX(order_date) FROM superstore;")
        min_date, max_date = cur.fetchone()
        print(f"Date range: {min_date} to {max_date}")

        cur.execute("SELECT SUM(sales), SUM(profit) FROM superstore;")
        total_sales, total_profit = cur.fetchone()
        print(f"Total Sales: ${total_sales:,.2f}, Total Profit: ${total_profit:,.2f}")


def main():
    """Main execution function."""
    print("=" * 50)
    print("Superstore Data Loader")
    print("=" * 50)

    if not CSV_PATH.exists():
        print(f"Error: CSV file not found at {CSV_PATH}")
        sys.exit(1)

    conn = get_connection(autocommit=False)
    try:
        create_table(conn)
        df = load_and_clean_data()
        insert_data(conn, df)
        verify_load(conn)
        print("\nLoad completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error during load: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
