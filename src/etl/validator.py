from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"


def load_data(filename, header=0):
    file = RAW_DATA / filename
    return pd.read_excel(file, header=header)


def check_primary_key(df, column_name):
    """
    DQ-01: Check duplicate primary keys.
    """
    duplicates = df[df[column_name].duplicated()]

    if duplicates.empty:
        print(f"✅ DQ-01 Passed ({column_name})")
    else:
        print(f"❌ DQ-01 Failed ({column_name})")
        print(duplicates)


def check_composite_key(df, columns):
    """
    DQ-02: Check duplicate composite keys.
    """
    duplicates = df[
        df.duplicated(subset=columns, keep=False)
    ]

    if duplicates.empty:
        print(f"✅ DQ-02 Passed {columns}")
    else:
        print(f"❌ DQ-02 Failed {columns}")
        print(f"Duplicate Records Found: {len(duplicates)}")
        print(duplicates[columns].drop_duplicates())
        print(f"Duplicate Records Found: {duplicates[columns].drop_duplicates().shape[0]}")

def check_foreign_key(parent_df, child_df, parent_key, child_key):
    """
    DQ-03: Check Foreign Key Integrity.
    """

    invalid_records = child_df[
        ~child_df[child_key].isin(parent_df[parent_key])
    ]

    if invalid_records.empty:
        print(f"✅ DQ-03 Passed ({child_key})")
    else:
        print(f"❌ DQ-03 Failed ({child_key})")
        unique_invalid = invalid_records[[child_key]].drop_duplicates()

        print(f"Invalid Company IDs Found: {len(unique_invalid)}")
        print(unique_invalid)

def check_balance_sheet(df):
    """
    DQ-04: Balance Sheet Validation
    Assets and Liabilities difference should be less than 1%.
    """

    difference = (
        (df["total_assets"] - df["total_liabilities"]).abs()
        / df["total_assets"]
    ) * 100

    failed = df[difference > 1]

    if failed.empty:
        print("✅ DQ-04 Passed (Balance Sheet Validation)")
    else:
        print("❌ DQ-04 Failed (Balance Sheet Validation)")
        print(f"Failed Records: {len(failed)}")
        print(failed[["company_id", "year", "total_assets", "total_liabilities"]].head())

def check_opm(df):
    """
    DQ-05: Operating Profit Margin Cross Check
    Formula:
    OPM = (Operating Profit / Sales) * 100
    """

# DQ-05 temporarily kept as-is.
# Source dataset contains inconsistent OPM values
# (e.g. 1353, 2307, -5715), requiring data cleaning
# before mathematical validation.

    calculated_opm = (df["operating_profit"] / df["sales"]) * 100

    difference = (calculated_opm - df["opm_percentage"]).abs()

    failed = df[difference > 1]

    if failed.empty:
        print("✅ DQ-05 Passed (OPM Cross Check)")
    else:
        print("❌ DQ-05 Failed (OPM Cross Check)")
        print(f"Failed Records: {len(failed)}")
        print(
            failed[
                [
                    "company_id",
                    "year",
                    "sales",
                    "operating_profit",
                    "opm_percentage",
                ]
            ].head()
        )
def check_positive_sales(df):
    """
    DQ-06: Sales should be greater than zero.
    """

    failed = df[df["sales"] <= 0]

    if failed.empty:
        print("✅ DQ-06 Passed (Positive Sales)")
    else:
        print("❌ DQ-06 Failed (Positive Sales)")
        print(f"Failed Records: {len(failed)}")
        print(
            failed[
                ["company_id", "year", "sales"]
            ]
        )

if __name__ == "__main__":

    companies = load_data("companies.xlsx", header=1)
    check_primary_key(companies, "id")

    profit_loss = load_data("profitandloss.xlsx", header=1)
    check_composite_key(
        profit_loss,
        ["company_id", "year"]
    )

    check_foreign_key(
        companies,
        profit_loss,
        "id",
        "company_id"
    )
    balance_sheet = load_data("balancesheet.xlsx", header=1)
    check_balance_sheet(balance_sheet)

    check_opm(profit_loss)
    check_positive_sales(profit_loss)
    
