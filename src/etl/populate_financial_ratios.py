from src.analytics.ratios import *
from src.analytics.cashflow_kpis import *
from pathlib import Path
import sqlite3
import pandas as pd

# ==========================================================
# DATABASE PATH
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"

# ==========================================================
# CONNECT DATABASE
# ==========================================================

conn = sqlite3.connect(DATABASE_FILE)

print("✅ Connected to Database")

# ==========================================================
# LOAD TABLES
# ==========================================================

profit_df = pd.read_sql("SELECT * FROM profitandloss", conn)
balance_df = pd.read_sql("SELECT * FROM balancesheet", conn)
cashflow_df = pd.read_sql("SELECT * FROM cashflow", conn)
company_df = pd.read_sql("SELECT * FROM companies", conn)

print(f"Profit & Loss Rows : {len(profit_df)}")
print(f"Balance Sheet Rows : {len(balance_df)}")
print(f"Cash Flow Rows     : {len(cashflow_df)}")
print(f"Companies Rows     : {len(company_df)}")

# ==========================================================
# REMOVE DUPLICATE COMPANY-YEAR RECORDS
# ==========================================================

profit_df = profit_df.drop_duplicates(
    subset=["company_id", "year"],
    keep="first"
)

balance_df = balance_df.drop_duplicates(
    subset=["company_id", "year"],
    keep="first"
)

cashflow_df = cashflow_df.drop_duplicates(
    subset=["company_id", "year"],
    keep="first"
)

print("\n✅ Duplicate company-year records removed.")

# ==========================================================
# MERGE TABLES
# ==========================================================

merged_df = pd.merge(
    profit_df,
    balance_df,
    on=["company_id", "year"],
    how="inner",
    suffixes=("_pl", "_bs")
)

merged_df = pd.merge(
    merged_df,
    cashflow_df,
    on=["company_id", "year"],
    how="left"
)

merged_df = pd.merge(
    merged_df,
    company_df,
    left_on="company_id",
    right_on="id",
    how="left",
    suffixes=("", "_company")
)

print("\n✅ Tables merged successfully")
print(f"Total merged rows : {len(merged_df)}")

print("\nColumns:")
print(list(merged_df.columns))

print("\nPreview:")
print(merged_df.head())

# ==========================================================
# GENERATE FINANCIAL RATIOS
# ==========================================================

ratio_records = []

for _, row in merged_df.iterrows():

    try:

        record = {

            "company_id": row["company_id"],
            "year": row["year"],

            # Profitability
            "net_profit_margin_pct": net_profit_margin(
                row["net_profit"],
                row["sales"]
            ),

            "operating_profit_margin_pct": operating_profit_margin(
                row["operating_profit"],
                row["sales"]
            ),

            "return_on_equity_pct": return_on_equity(
                row["net_profit"],
                row["equity_capital"],
                row["reserves"]
            ),

            # Leverage
            "debt_to_equity": debt_to_equity(
                row["borrowings"],
                row["equity_capital"],
                row["reserves"]
            ),

            "interest_coverage": interest_coverage_ratio(
                row["operating_profit"],
                row["other_income"],
                row["interest"]
            ),

            # Efficiency
            "asset_turnover": asset_turnover(
                row["sales"],
                row["total_assets"]
            ),

            # Cash Flow
            "free_cash_flow_cr": free_cash_flow(
                row["operating_activity"],
                abs(row["investing_activity"])
            ),

            # Direct values
            "capex_cr": abs(row["investing_activity"]),

            "earnings_per_share": row["eps"],

            "book_value_per_share": row["book_value"],

            "dividend_payout_ratio_pct": row["dividend_payout"],

            "total_debt_cr": row["borrowings"],

            "cash_from_operations_cr": row["operating_activity"]

        }

        ratio_records.append(record)

    except Exception as e:
        print(f"Skipped {row['company_id']} {row['year']} : {e}")

ratio_df = pd.DataFrame(ratio_records)

print("\n===================================")
print("FINANCIAL RATIOS GENERATED")
print("===================================")

print(f"Rows Generated : {len(ratio_df)}")
print(ratio_df.head())

# ==========================================================
# POPULATE financial_ratios TABLE
# ==========================================================

print("\nClearing existing financial_ratios table...")

conn = sqlite3.connect(DATABASE_FILE)

conn.execute("DELETE FROM financial_ratios")
conn.commit()

print("Existing records deleted.")

ratio_df.insert(
    0,
    "id",
    range(1, len(ratio_df) + 1)
)

ratio_df.to_sql(
    "financial_ratios",
    conn,
    if_exists="append",
    index=False
)

conn.commit()

print("Financial ratios inserted successfully.")

# ==========================================================
# VERIFY INSERT
# ==========================================================

count = conn.execute(
    "SELECT COUNT(*) FROM financial_ratios"
).fetchone()[0]

print("\n===================================")
print("DATABASE VERIFICATION")
print("===================================")

print(f"Rows in financial_ratios : {count}")

print("\nSample Records:\n")

sample = pd.read_sql(
    """
    SELECT *
    FROM financial_ratios
    LIMIT 10
    """,
    conn
)

print(sample)
conn.close()