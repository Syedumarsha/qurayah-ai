
import sqlite3
from pathlib import Path

# Locate the SQLite database
BASE_DIR = Path(__file__).resolve().parent.parent

DB_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "translations"
    / "english_saheeh.sqlite"
)

# Check whether the database exists
if not DB_FILE.exists():
    print("Error: Translation database not found!")
    raise SystemExit(1)

try:
    # Open database in read-only mode
    connection = sqlite3.connect(
        DB_FILE.as_uri() + "?mode=ro",
        uri=True
    )

    cursor = connection.cursor()

    # Find all database tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """)

    tables = cursor.fetchall()

    print("Translation database opened successfully!")
    print("------------------------------------------")

    print("\nAvailable tables:")

    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")

        # Inspect table columns
        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns = cursor.fetchall()

        for column in columns:
            print(f"  Column: {column[1]} | Type: {column[2]}")

        # Display two sample records
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 2')

        records = cursor.fetchall()

        print("\nSample records:")

        for record in records:
            print(record)

    connection.close()

except sqlite3.Error as error:
    print("Database error:", error)
