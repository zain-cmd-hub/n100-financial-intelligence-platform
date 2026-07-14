import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"

connection = sqlite3.connect(DATABASE_FILE)

tables = connection.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name NOT LIKE 'sqlite_%'
    ORDER BY name;
    """
).fetchall()

print("\nDatabase Table Row Counts")
print("=" * 40)

for table in tables:
    table_name = table[0]

    count = connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]

    print(f"{table_name}: {count}")

connection.close()