from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"

conn = sqlite3.connect(DATABASE_FILE)

df = pd.read_sql(
    "SELECT * FROM financial_ratios",
    conn
)

print("Financial Ratios Loaded :", len(df))

# ==========================================================
# MISSING VALUE CHECK
# ==========================================================

print("\n==============================")
print("MISSING VALUE CHECK")
print("==============================")

missing = df.isnull().sum()
print(missing)

# ==========================================================
# INFINITE VALUE CHECK
# ==========================================================

print("\n==============================")
print("INFINITE VALUE CHECK")
print("==============================")

numeric = df.select_dtypes(include=np.number)

inf_count = np.isinf(numeric).sum()
print(inf_count)

# ==========================================================
# DUPLICATE CHECK
# ==========================================================

print("\n==============================")
print("DUPLICATE CHECK")
print("==============================")

duplicates = df.duplicated(
    subset=["company_id", "year"]
).sum()

print("Duplicate Records :", duplicates)

# ==========================================================
# NEGATIVE DEBT TO EQUITY
# ==========================================================

print("\n==============================")
print("NEGATIVE DEBT TO EQUITY")
print("==============================")

negative_de = df[df["debt_to_equity"] < 0]

print("Negative Debt/Equity :", len(negative_de))

# ==========================================================
# NEGATIVE INTEREST COVERAGE
# ==========================================================

print("\n==============================")
print("NEGATIVE INTEREST COVERAGE")
print("==============================")

negative_icr = df[df["interest_coverage"] < 0]

print("Negative ICR :", len(negative_icr))

if len(negative_icr) > 0:
    print("\nCompanies with Negative Interest Coverage:")
    print(
    negative_icr[
        [
            "company_id",
            "year",
            "interest_coverage",
            "total_debt_cr",
            "cash_from_operations_cr"
        ]
    ].head(10)
)

# ==========================================================
# EXPORT VALIDATION REPORT
# ==========================================================

summary = pd.DataFrame({
    "Check": [
        "Rows",
        "Duplicate Records",
        "Negative Debt/Equity",
        "Negative Interest Coverage"
    ],
    "Value": [
        len(df),
        duplicates,
        len(negative_de),
        len(negative_icr)
    ]
})

reports_dir = BASE_DIR / "reports"
reports_dir.mkdir(exist_ok=True)

report_path = reports_dir / "financial_ratios_validation_report.csv"

summary.to_csv(
    report_path,
    index=False
)

print("\n====================================")
print("VALIDATION SUMMARY")
print("====================================")
print(summary)

print(f"\nValidation report saved to:\n{report_path}")

print("\n==============================")
print("MISSING VALUE SUMMARY")
print("==============================")

missing_summary = missing[missing > 0]

if len(missing_summary) == 0:
    print("No missing values found.")
else:
    print(missing_summary)

conn.close()