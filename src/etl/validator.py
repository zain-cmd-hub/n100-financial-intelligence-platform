from pathlib import Path
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

# Stores all failed validation records
validation_failures = []


# ============================================================
# DATA LOADER
# ============================================================

def load_data(filename, header=0):
    """
    Load an Excel file from the raw data directory.
    """
    file = RAW_DATA / filename
    return pd.read_excel(file, header=header)


# ============================================================
# FAILURE LOGGER
# ============================================================

def record_failure(dq_rule, severity, description, failed_df):
    """
    Store failed validation records for the final CSV report.
    """

    if failed_df.empty:
        return

    for _, row in failed_df.iterrows():

        validation_failures.append({
            "dq_rule": dq_rule,
            "severity": severity,
            "description": description,
            "company_id": row.get(
                "company_id",
                row.get("id", "")
            ),
            "year": row.get(
                "year",
                row.get("Year", "")
            )
        })


# ============================================================
# DQ-01: PRIMARY KEY VALIDATION
# ============================================================

def check_primary_key(df, column_name):
    """
    DQ-01: Check duplicate primary keys.
    """

    duplicates = df[
        df[column_name].duplicated(keep=False)
    ]

    if duplicates.empty:

        print(f"✅ DQ-01 Passed ({column_name})")

    else:

        print(f"❌ DQ-01 Failed ({column_name})")
        print(f"Duplicate Records Found: {len(duplicates)}")

        print(
            duplicates[
                [column_name]
            ].drop_duplicates()
        )

        record_failure(
            "DQ-01",
            "CRITICAL",
            "Duplicate primary key detected",
            duplicates
        )


# ============================================================
# DQ-02: COMPOSITE KEY VALIDATION
# ============================================================

def check_composite_key(df, columns):
    """
    DQ-02: Check duplicate composite keys.
    """

    duplicates = df[
        df.duplicated(
            subset=columns,
            keep=False
        )
    ]

    if duplicates.empty:

        print(f"✅ DQ-02 Passed {columns}")

    else:

        unique_duplicates = (
            duplicates[columns]
            .drop_duplicates()
        )

        print(f"❌ DQ-02 Failed {columns}")
        print(
            f"Duplicate Records Found: "
            f"{len(duplicates)}"
        )

        print(unique_duplicates)

        print(
            f"Duplicate Keys Found: "
            f"{len(unique_duplicates)}"
        )

        record_failure(
            "DQ-02",
            "CRITICAL",
            "Duplicate company-year composite key",
            duplicates
        )


# ============================================================
# DQ-03: FOREIGN KEY VALIDATION
# ============================================================

def check_foreign_key(
    parent_df,
    child_df,
    parent_key,
    child_key
):
    """
    DQ-03: Check Foreign Key Integrity.
    """

    invalid_records = child_df[
        ~child_df[child_key].isin(
            parent_df[parent_key]
        )
    ]

    if invalid_records.empty:

        print(
            f"✅ DQ-03 Passed ({child_key})"
        )

    else:

        unique_invalid = (
            invalid_records[[child_key]]
            .drop_duplicates()
        )

        print(
            f"❌ DQ-03 Failed ({child_key})"
        )

        print(
            f"Invalid Company IDs Found: "
            f"{len(unique_invalid)}"
        )

        print(unique_invalid)

        record_failure(
            "DQ-03",
            "CRITICAL",
            "Foreign key company_id not found in companies table",
            invalid_records
        )


# ============================================================
# DQ-04: BALANCE SHEET VALIDATION
# ============================================================

def check_balance_sheet(df):
    """
    DQ-04: Assets and liabilities difference
    should not exceed 1%.
    """

    valid_assets = (
        df["total_assets"].notna()
        & (df["total_assets"] != 0)
    )

    difference = pd.Series(
        float("nan"),
        index=df.index
    )

    difference.loc[valid_assets] = (
        (
            df.loc[valid_assets, "total_assets"]
            - df.loc[valid_assets, "total_liabilities"]
        ).abs()
        / df.loc[valid_assets, "total_assets"].abs()
    ) * 100

    failed = df[
        valid_assets
        & (difference > 1)
    ]

    if failed.empty:

        print(
            "✅ DQ-04 Passed "
            "(Balance Sheet Validation)"
        )

    else:

        print(
            "❌ DQ-04 Failed "
            "(Balance Sheet Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "total_assets",
                    "total_liabilities"
                ]
            ].head()
        )

        record_failure(
            "DQ-04",
            "WARNING",
            "Assets and liabilities difference exceeds 1 percent",
            failed
        )


# ============================================================
# DQ-05: OPM CROSS CHECK
# ============================================================

def check_opm(df):
    """
    DQ-05: Operating Profit Margin Cross Check.

    Formula:
    OPM = (Operating Profit / Sales) * 100
    """

    # Source data contains some inconsistent OPM values.
    # The validator reports those inconsistencies.

    valid_sales = (
        df["sales"].notna()
        & (df["sales"] != 0)
    )

    calculated_opm = pd.Series(
        float("nan"),
        index=df.index
    )

    calculated_opm.loc[valid_sales] = (
        df.loc[
            valid_sales,
            "operating_profit"
        ]
        / df.loc[
            valid_sales,
            "sales"
        ]
    ) * 100

    difference = (
        calculated_opm
        - df["opm_percentage"]
    ).abs()

    failed = df[
        valid_sales
        & (difference > 1)
    ]

    if failed.empty:

        print(
            "✅ DQ-05 Passed "
            "(OPM Cross Check)"
        )

    else:

        print(
            "❌ DQ-05 Failed "
            "(OPM Cross Check)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "sales",
                    "operating_profit",
                    "opm_percentage"
                ]
            ].head()
        )

        record_failure(
            "DQ-05",
            "WARNING",
            "Operating profit margin does not match calculated OPM",
            failed
        )


# ============================================================
# DQ-06: POSITIVE SALES VALIDATION
# ============================================================

def check_positive_sales(df):
    """
    DQ-06: Sales should be greater than zero.
    """

    failed = df[
        df["sales"].notna()
        & (df["sales"] <= 0)
    ]

    if failed.empty:

        print(
            "✅ DQ-06 Passed "
            "(Positive Sales)"
        )

    else:

        print(
            "❌ DQ-06 Failed "
            "(Positive Sales)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "sales"
                ]
            ]
        )

        record_failure(
            "DQ-06",
            "WARNING",
            "Sales must be greater than zero",
            failed
        )


# ============================================================
# DQ-07: NET CASH FLOW VALIDATION
# ============================================================

def check_net_cash_flow(df):
    """
    DQ-07: Net Cash Flow Cross Check.

    Net Cash Flow =
    Operating Activity
    + Investing Activity
    + Financing Activity
    """

    calculated_net_cash = (
        df["operating_activity"].fillna(0)
        + df["investing_activity"].fillna(0)
        + df["financing_activity"].fillna(0)
    )

    difference = (
        calculated_net_cash
        - df["net_cash_flow"]
    ).abs()

    failed = df[
        df["net_cash_flow"].notna()
        & (difference > 1)
    ]

    if failed.empty:

        print(
            "✅ DQ-07 Passed "
            "(Net Cash Flow Cross Check)"
        )

    else:

        print(
            "❌ DQ-07 Failed "
            "(Net Cash Flow Cross Check)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "operating_activity",
                    "investing_activity",
                    "financing_activity",
                    "net_cash_flow"
                ]
            ].head()
        )

        record_failure(
            "DQ-07",
            "WARNING",
            "Net cash flow does not match operating, investing and financing activities",
            failed
        )


# ============================================================
# DQ-08: TAX RATE VALIDATION
# ============================================================

def check_tax_rate(df):
    """
    DQ-08: Tax percentage should be
    between 0 and 100.
    """

    failed = df[
        df["tax_percentage"].notna()
        & (
            (df["tax_percentage"] < 0)
            | (df["tax_percentage"] > 100)
        )
    ]

    if failed.empty:

        print(
            "✅ DQ-08 Passed "
            "(Tax Rate Validation)"
        )

    else:

        print(
            "❌ DQ-08 Failed "
            "(Tax Rate Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "tax_percentage"
                ]
            ].head()
        )

        record_failure(
            "DQ-08",
            "WARNING",
            "Tax percentage is outside the expected 0 to 100 range",
            failed
        )


# ============================================================
# DQ-09: DIVIDEND PAYOUT VALIDATION
# ============================================================

def check_dividend_payout(df):
    """
    DQ-09: Dividend payout should be
    between 0 and 100.
    """

    failed = df[
        df["dividend_payout"].notna()
        & (
            (df["dividend_payout"] < 0)
            | (df["dividend_payout"] > 100)
        )
    ]

    if failed.empty:

        print(
            "✅ DQ-09 Passed "
            "(Dividend Payout Validation)"
        )

    else:

        print(
            "❌ DQ-09 Failed "
            "(Dividend Payout Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "dividend_payout"
                ]
            ].head()
        )

        record_failure(
            "DQ-09",
            "WARNING",
            "Dividend payout is outside the expected 0 to 100 range",
            failed
        )


# ============================================================
# DQ-10: EPS SIGN CONSISTENCY
# ============================================================

def check_eps_sign(df):
    """
    DQ-10: Net Profit and EPS should
    have consistent signs.
    """

    failed = df[
        df["net_profit"].notna()
        & df["eps"].notna()
        & (
            (
                (df["net_profit"] > 0)
                & (df["eps"] < 0)
            )
            |
            (
                (df["net_profit"] < 0)
                & (df["eps"] > 0)
            )
        )
    ]

    if failed.empty:

        print(
            "✅ DQ-10 Passed "
            "(EPS Sign Consistency)"
        )

    else:

        print(
            "❌ DQ-10 Failed "
            "(EPS Sign Consistency)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "year",
                    "net_profit",
                    "eps"
                ]
            ].head()
        )

        record_failure(
            "DQ-10",
            "WARNING",
            "EPS and net profit signs are inconsistent",
            failed
        )


# ============================================================
# DQ-11: ANNUAL REPORT URL VALIDATION
# ============================================================

def check_annual_report_url(df):
    """
    DQ-11: Annual Report URL must be
    present and start with http or https.
    """

    url_pattern = r"^https?://"

    failed = df[
        df["Annual_Report"].isna()
        | ~df["Annual_Report"]
            .astype(str)
            .str.strip()
            .str.match(
                url_pattern,
                na=False
            )
    ]

    if failed.empty:

        print(
            "✅ DQ-11 Passed "
            "(Annual Report URL Validation)"
        )

    else:

        print(
            "❌ DQ-11 Failed "
            "(Annual Report URL Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "company_id",
                    "Year",
                    "Annual_Report"
                ]
            ].head()
        )

        record_failure(
            "DQ-11",
            "WARNING",
            "Annual report URL is missing or invalid",
            failed
        )


# ============================================================
# DQ-12: BSE PROFILE URL VALIDATION
# ============================================================

def check_bse_profile(df):
    """
    DQ-12: BSE Profile URL must be
    present and valid.
    """

    failed = df[
        df["bse_profile"].isna()
        | ~df["bse_profile"]
            .astype(str)
            .str.strip()
            .str.match(
                r"^https?://",
                na=False
            )
    ]

    if failed.empty:

        print(
            "✅ DQ-12 Passed "
            "(BSE Profile URL Validation)"
        )

    else:

        print(
            "❌ DQ-12 Failed "
            "(BSE Profile URL Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "id",
                    "company_name",
                    "bse_profile"
                ]
            ].head()
        )

        record_failure(
            "DQ-12",
            "WARNING",
            "BSE profile URL is missing or invalid",
            failed
        )


# ============================================================
# DQ-13: HISTORICAL DATA COVERAGE
# ============================================================

def check_data_coverage(
    df,
    minimum_years=5
):
    """
    DQ-13: Each company should have
    at least 5 unique financial years.
    """

    coverage = (
        df.groupby("company_id")["year"]
        .nunique()
        .reset_index(
            name="year_count"
        )
    )

    failed = coverage[
        coverage["year_count"]
        < minimum_years
    ]

    if failed.empty:

        print(
            f"✅ DQ-13 Passed "
            f"(Minimum {minimum_years}-Year "
            f"Data Coverage)"
        )

    else:

        print(
            f"❌ DQ-13 Failed "
            f"(Minimum {minimum_years}-Year "
            f"Data Coverage)"
        )

        print(
            f"Failed Companies: "
            f"{len(failed)}"
        )

        print(
            failed.head()
        )

        record_failure(
            "DQ-13",
            "WARNING",
            f"Company has less than {minimum_years} years of financial data",
            failed
        )


# ============================================================
# DQ-14: ROE RANGE VALIDATION
# ============================================================

def check_roe_range(df):
    """
    DQ-14: ROE percentage should be
    within -100 and 100.
    """

    failed = df[
        df["roe_percentage"].notna()
        & (
            (df["roe_percentage"] < -100)
            | (df["roe_percentage"] > 100)
        )
    ]

    if failed.empty:

        print(
            "✅ DQ-14 Passed "
            "(ROE Range Validation)"
        )

    else:

        print(
            "❌ DQ-14 Failed "
            "(ROE Range Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "id",
                    "company_name",
                    "roe_percentage"
                ]
            ].head()
        )

        record_failure(
            "DQ-14",
            "WARNING",
            "ROE percentage is outside the expected -100 to 100 range",
            failed
        )


# ============================================================
# DQ-15: NSE PROFILE URL VALIDATION
# ============================================================

def check_nse_profile(df):
    """
    DQ-15: NSE Profile URL must be
    present and valid.
    """

    failed = df[
        df["nse_profile"].isna()
        | ~df["nse_profile"]
            .astype(str)
            .str.strip()
            .str.match(
                r"^https?://",
                na=False
            )
    ]

    if failed.empty:

        print(
            "✅ DQ-15 Passed "
            "(NSE Profile URL Validation)"
        )

    else:

        print(
            "❌ DQ-15 Failed "
            "(NSE Profile URL Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "id",
                    "company_name",
                    "nse_profile"
                ]
            ].head()
        )

        record_failure(
            "DQ-15",
            "WARNING",
            "NSE profile URL is missing or invalid",
            failed
        )


# ============================================================
# DQ-16: COMPANY WEBSITE URL VALIDATION
# ============================================================

def check_company_website(df):
    """
    DQ-16: Company Website URL must be
    present and valid.
    """

    failed = df[
        df["website"].isna()
        | ~df["website"]
            .astype(str)
            .str.strip()
            .str.match(
                r"^https?://",
                na=False
            )
    ]

    if failed.empty:

        print(
            "✅ DQ-16 Passed "
            "(Company Website URL Validation)"
        )

    else:

        print(
            "❌ DQ-16 Failed "
            "(Company Website URL Validation)"
        )

        print(
            f"Failed Records: {len(failed)}"
        )

        print(
            failed[
                [
                    "id",
                    "company_name",
                    "website"
                ]
            ].head()
        )

        record_failure(
            "DQ-16",
            "WARNING",
            "Company website URL is missing or invalid",
            failed
        )


# ============================================================
# MAIN EXECUTION
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("NIFTY 100 DATA QUALITY VALIDATION")
    print("=" * 60)

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    companies = load_data(
        "companies.xlsx",
        header=1
    )

    profit_loss = load_data(
        "profitandloss.xlsx",
        header=1
    )

    balance_sheet = load_data(
        "balancesheet.xlsx",
        header=1
    )

    cashflow = load_data(
        "cashflow.xlsx",
        header=1
    )

    documents = load_data(
        "documents.xlsx",
        header=1
    )

    # --------------------------------------------------------
    # Run DQ validations
    # --------------------------------------------------------

    check_primary_key(
        companies,
        "id"
    )

    check_composite_key(
        profit_loss,
        [
            "company_id",
            "year"
        ]
    )

    check_foreign_key(
        companies,
        profit_loss,
        "id",
        "company_id"
    )

    check_balance_sheet(
        balance_sheet
    )

    check_opm(
        profit_loss
    )

    check_positive_sales(
        profit_loss
    )

    check_net_cash_flow(
        cashflow
    )

    check_tax_rate(
        profit_loss
    )

    check_dividend_payout(
        profit_loss
    )

    check_eps_sign(
        profit_loss
    )

    check_annual_report_url(
        documents
    )

    check_bse_profile(
        companies
    )

    check_data_coverage(
        profit_loss
    )

    check_roe_range(
        companies
    )

    check_nse_profile(
        companies
    )

    check_company_website(
        companies
    )

    # --------------------------------------------------------
    # Save final validation report
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    failures_df = pd.DataFrame(
        validation_failures
    )

    output_file = (
        OUTPUT_DIR
        / "validation_failures.csv"
    )

    failures_df.to_csv(
        output_file,
        index=False
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Validation report saved successfully"
    )

    print(
        f"File: {output_file}"
    )

    print(
        f"Total failures logged: "
        f"{len(failures_df)}"
    )

    print("=" * 60)