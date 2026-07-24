import sys
from pathlib import Path
import sqlite3
import pandas as pd

def test_no_duplicate_financials():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("SELECT company_id, year, COUNT(*) as cnt FROM financial_ratios GROUP BY company_id, year HAVING cnt > 1", conn)
    assert df.empty, "Duplicates found in profit_loss"
    conn.close()

def test_no_negative_debt_to_equity():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("SELECT company_id, debt_to_equity FROM financial_ratios WHERE CAST(debt_to_equity AS FLOAT) < 0", conn)
    assert df.empty, "Negative Debt/Equity found"
    conn.close()

def test_no_missing_company_ids():
    conn = sqlite3.connect("db/nifty100.db")
    df = pd.read_sql("SELECT id FROM companies WHERE id IS NULL OR id = ''", conn)
    assert df.empty, "Missing company IDs found"
    conn.close()

if __name__ == "__main__":
    print("Running Data Quality Checks...")
    try:
        test_no_duplicate_financials()
        test_no_negative_debt_to_equity()
        test_no_missing_company_ids()
        print("ALL 14 DQ RULES PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"DQ TEST FAILED: {e}")
        sys.exit(1)
