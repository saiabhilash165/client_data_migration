import sqlite3
import pandas as pd

conn = sqlite3.connect("migration.db")

df = pd.read_sql_query(
    """
    SELECT *
    FROM sales_deals
    ORDER BY id
    """,
    conn
)

print(df)

conn.close()