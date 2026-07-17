from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"

conn = sqlite3.connect(DATABASE_FILE)

tables = [
    "companies",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "financial_ratios"
]

print("=" * 50)
print("FINAL PIPELINE VERIFICATION")
print("=" * 50)

summary = []

for table in tables:
    count = conn.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    summary.append({
        "Table": table,
        "Rows": count
    })

summary_df = pd.DataFrame(summary)

print(summary_df)

conn.close()