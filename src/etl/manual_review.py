from pathlib import Path
import sqlite3
import random

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"

REVIEW_FILE = OUTPUT_DIR / "manual_review.csv"
COVERAGE_FILE = OUTPUT_DIR / "year_coverage.csv"


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42
SAMPLE_SIZE = 5


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect_database():
    """
    Connect to the SQLite database and enable
    foreign key enforcement.
    """

    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    connection = sqlite3.connect(DATABASE_FILE)

    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    return connection


# ============================================================
# FOREIGN KEY CHECK
# ============================================================

def check_foreign_keys(connection):
    """
    Run SQLite foreign key integrity check.
    """

    violations = connection.execute(
        "PRAGMA foreign_key_check;"
    ).fetchall()

    print("\n" + "=" * 70)
    print("1. FOREIGN KEY INTEGRITY CHECK")
    print("=" * 70)

    if not violations:
        print("✅ PASS — 0 foreign key violations")
    else:
        print(
            f"❌ FAIL — {len(violations)} "
            f"foreign key violations found"
        )

        for violation in violations[:10]:
            print(violation)

    return len(violations)


# ============================================================
# GET MASTER COMPANIES
# ============================================================

def get_companies(connection):
    """
    Get all companies from the master table.
    """

    return pd.read_sql_query(
        """
        SELECT
            id AS company_id,
            company_name
        FROM companies
        ORDER BY id;
        """,
        connection
    )


# ============================================================
# RANDOM COMPANY REVIEW
# ============================================================

def review_random_companies(connection):
    """
    Select 5 reproducible random companies and review
    their data across major financial tables.
    """

    companies = get_companies(connection)

    random.seed(RANDOM_SEED)

    sample_size = min(
        SAMPLE_SIZE,
        len(companies)
    )

    selected_ids = random.sample(
        companies["company_id"].tolist(),
        sample_size
    )

    selected_companies = companies[
        companies["company_id"].isin(selected_ids)
    ].copy()

    print("\n" + "=" * 70)
    print("2. MANUAL REVIEW — 5 RANDOM COMPANIES")
    print("=" * 70)

    review_records = []

    for _, company in selected_companies.iterrows():

        company_id = company["company_id"]
        company_name = company["company_name"]

        print(
            f"\n🔎 Reviewing: "
            f"{company_id} — {company_name}"
        )

        # --------------------------------------------
        # Profit & Loss
        # --------------------------------------------

        pnl = pd.read_sql_query(
            """
            SELECT
                year,
                sales,
                operating_profit,
                net_profit,
                eps
            FROM profitandloss
            WHERE company_id = ?
            ORDER BY year;
            """,
            connection,
            params=(company_id,)
        )

        # --------------------------------------------
        # Balance Sheet
        # --------------------------------------------

        balance_sheet = pd.read_sql_query(
            """
            SELECT
                year,
                total_assets,
                total_liabilities
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY year;
            """,
            connection,
            params=(company_id,)
        )

        # --------------------------------------------
        # Cash Flow
        # --------------------------------------------

        cashflow = pd.read_sql_query(
            """
            SELECT
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            WHERE company_id = ?
            ORDER BY year;
            """,
            connection,
            params=(company_id,)
        )

        # --------------------------------------------
        # Stock Prices
        # --------------------------------------------

        stock_prices = pd.read_sql_query(
            """
            SELECT
                date,
                close_price
            FROM stock_prices
            WHERE company_id = ?
            ORDER BY date;
            """,
            connection,
            params=(company_id,)
        )

        pnl_rows = len(pnl)
        bs_rows = len(balance_sheet)
        cf_rows = len(cashflow)
        price_rows = len(stock_prices)

        print(f"   P&L rows:          {pnl_rows}")
        print(f"   Balance Sheet:     {bs_rows}")
        print(f"   Cash Flow:         {cf_rows}")
        print(f"   Stock Price rows:  {price_rows}")

        status = (
            "PASS"
            if (
                pnl_rows > 0
                and bs_rows > 0
                and cf_rows > 0
                and price_rows > 0
            )
            else "REVIEW"
        )

        print(
            f"   Status: "
            f"{'✅ PASS' if status == 'PASS' else '⚠ REVIEW'}"
        )

        review_records.append(
            {
                "company_id": company_id,
                "company_name": company_name,
                "profitandloss_rows": pnl_rows,
                "balancesheet_rows": bs_rows,
                "cashflow_rows": cf_rows,
                "stock_price_rows": price_rows,
                "review_status": status,
            }
        )

    review_df = pd.DataFrame(
        review_records
    )

    review_df.to_csv(
        REVIEW_FILE,
        index=False
    )

    print(
        f"\n✅ Manual review report saved: "
        f"{REVIEW_FILE}"
    )

    return review_df


# ============================================================
# YEAR COVERAGE CHECK
# ============================================================

def check_year_coverage(connection):
    """
    Check company year coverage using Profit & Loss data.

    Companies with fewer than 5 distinct financial years
    are flagged for review.
    """

    coverage = pd.read_sql_query(
        """
        SELECT
            c.id AS company_id,
            c.company_name,
            COUNT(
                DISTINCT p.year
            ) AS year_count
        FROM companies c

        LEFT JOIN profitandloss p
            ON c.id = p.company_id

        GROUP BY
            c.id,
            c.company_name

        ORDER BY
            year_count ASC,
            c.id ASC;
        """,
        connection
    )

    coverage["coverage_status"] = coverage[
        "year_count"
    ].apply(
        lambda value:
        "PASS"
        if value >= 5
        else "REVIEW"
    )

    coverage.to_csv(
        COVERAGE_FILE,
        index=False
    )

    failed = coverage[
        coverage["year_count"] < 5
    ]

    print("\n" + "=" * 70)
    print("3. MINIMUM 5-YEAR DATA COVERAGE")
    print("=" * 70)

    if failed.empty:

        print(
            "✅ PASS — All companies have "
            "at least 5 years of P&L data"
        )

    else:

        print(
            f"⚠ REVIEW — {len(failed)} companies "
            f"have less than 5 years of data"
        )

        print(
            failed[
                [
                    "company_id",
                    "company_name",
                    "year_count"
                ]
            ].to_string(
                index=False
            )
        )

    print(
        f"\n✅ Year coverage report saved: "
        f"{COVERAGE_FILE}"
    )

    return coverage


# ============================================================
# DATABASE ROW COUNTS
# ============================================================

def check_table_row_counts(connection):
    """
    Print row counts for all database tables.
    """

    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
        """
    ).fetchall()

    print("\n" + "=" * 70)
    print("4. FINAL DATABASE ROW COUNTS")
    print("=" * 70)

    counts = {}

    for table in tables:

        table_name = table[0]

        count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM {table_name};
            """
        ).fetchone()[0]

        counts[table_name] = count

        print(
            f"{table_name:<20} "
            f"{count}"
        )

    return counts


# ============================================================
# DAY 6 FINAL SUMMARY
# ============================================================

def print_summary(
    fk_violations,
    review_df,
    coverage
):
    """
    Print Day 6 final review summary.
    """

    manual_pass = int(
        (
            review_df[
                "review_status"
            ] == "PASS"
        ).sum()
    )

    manual_review = int(
        (
            review_df[
                "review_status"
            ] == "REVIEW"
        ).sum()
    )

    under_5_years = int(
        (
            coverage[
                "year_count"
            ] < 5
        ).sum()
    )

    print("\n" + "=" * 70)
    print("DAY 6 — DATA QUALITY MANUAL REVIEW SUMMARY")
    print("=" * 70)

    print(
        f"Foreign key violations: "
        f"{fk_violations}"
    )

    print(
        f"Random companies reviewed: "
        f"{len(review_df)}"
    )

    print(
        f"Manual review PASS: "
        f"{manual_pass}"
    )

    print(
        f"Manual review REVIEW: "
        f"{manual_review}"
    )

    print(
        f"Companies with <5 years: "
        f"{under_5_years}"
    )

    print(
        "\n✅ Day 6 manual review execution completed."
    )

    if (
        fk_violations == 0
        and manual_review == 0
    ):

        print(
            "✅ Database integrity and sampled "
            "company data look consistent."
        )

    if under_5_years > 0:

        print(
            "⚠ Companies with limited historical data "
            "remain documented for review."
        )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = connect_database()

    try:

        fk_violations = (
            check_foreign_keys(
                connection
            )
        )

        review_df = (
            review_random_companies(
                connection
            )
        )

        coverage = (
            check_year_coverage(
                connection
            )
        )

        check_table_row_counts(
            connection
        )

        print_summary(
            fk_violations,
            review_df,
            coverage
        )

    finally:

        connection.close()


if __name__ == "__main__":
    main()