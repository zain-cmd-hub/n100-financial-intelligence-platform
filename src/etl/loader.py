from pathlib import Path
from datetime import datetime
import sqlite3

import pandas as pd

from normaliser import normalize_ticker


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA = BASE_DIR / "data" / "raw"
DB_DIR = BASE_DIR / "db"
OUTPUT_DIR = BASE_DIR / "output"

SCHEMA_FILE = DB_DIR / "schema.sql"
DATABASE_FILE = DB_DIR / "nifty100.db"
AUDIT_FILE = OUTPUT_DIR / "load_audit.csv"


# ============================================================
# DATASET CONFIGURATION
# ============================================================

# Load order matters:
# companies must be loaded first because all child tables
# reference companies(id).

DATASETS = [
    {
        "file": "companies.xlsx",
        "table": "companies",
        "header": 1,
    },
    {
        "file": "profitandloss.xlsx",
        "table": "profitandloss",
        "header": 1,
    },
    {
        "file": "balancesheet.xlsx",
        "table": "balancesheet",
        "header": 1,
    },
    {
        "file": "cashflow.xlsx",
        "table": "cashflow",
        "header": 1,
    },
    {
        "file": "analysis.xlsx",
        "table": "analysis",
        "header": 1,
    },
    {
        "file": "documents.xlsx",
        "table": "documents",
        "header": 1,
    },
    {
        "file": "prosandcons.xlsx",
        "table": "prosandcons",
        "header": 1,
    },
    {
        "file": "sectors.xlsx",
        "table": "sectors",
        "header": 0,
    },
    {
        "file": "stock_prices.xlsx",
        "table": "stock_prices",
        "header": 0,
    },
    {
        "file": "market_cap.xlsx",
        "table": "market_cap",
        "header": 0,
    },
    {
        "file": "financial_ratios.xlsx",
        "table": "financial_ratios",
        "header": 0,
    },
    {
        "file": "peer_groups.xlsx",
        "table": "peer_groups",
        "header": 0,
    },
]


# ============================================================
# DATA CLEANING FUNCTIONS
# ============================================================

def clean_column_names(df):
    """
    Standardize DataFrame column names.
    """

    df.columns = [
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        for column in df.columns
    ]

    return df


def clean_text_columns(df):
    """
    Remove leading and trailing spaces from text columns.
    """

    for column in df.columns:

        if (
            pd.api.types.is_object_dtype(df[column])
            or pd.api.types.is_string_dtype(df[column])
        ):

            df[column] = df[column].apply(
                lambda value:
                value.strip()
                if isinstance(value, str)
                else value
            )

    return df


def normalize_company_ids(df):
    """
    Normalize company ticker symbols.

    Example:
    AGTL -> ADANIGREEN
    """

    if "company_id" in df.columns:

        df["company_id"] = df[
            "company_id"
        ].apply(
            normalize_ticker
        )

    return df


# ============================================================
# EXCEL LOADER
# ============================================================

def load_excel(filename, header):
    """
    Load and clean one Excel source file.
    """

    file_path = RAW_DATA / filename

    if not file_path.exists():

        raise FileNotFoundError(
            f"Source file not found: {file_path}"
        )

    df = pd.read_excel(
        file_path,
        header=header
    )

    # Standardize columns
    df = clean_column_names(df)

    # Clean text
    df = clean_text_columns(df)

    # Normalize company tickers
    df = normalize_company_ids(df)

    return df


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_table_columns(
    connection,
    table_name
):
    """
    Return column names from an SQLite table.
    """

    result = connection.execute(
        f"PRAGMA table_info({table_name});"
    ).fetchall()

    return [
        row[1]
        for row in result
    ]


def align_dataframe_to_table(
    connection,
    df,
    table_name
):
    """
    Keep only columns that exist in the database table.
    """

    table_columns = get_table_columns(
        connection,
        table_name
    )

    source_columns = df.columns.tolist()

    matching_columns = [
        column
        for column in table_columns
        if column in source_columns
    ]

    if not matching_columns:

        raise ValueError(
            f"No matching columns found "
            f"for table: {table_name}"
        )

    return df[
        matching_columns
    ].copy()


# ============================================================
# DUPLICATE PRIMARY KEY CHECK
# ============================================================

def remove_duplicate_primary_keys(
    df,
    table_name
):
    """
    Remove duplicate ID primary keys.

    First occurrence is retained.
    """

    if "id" not in df.columns:
        return df, 0

    duplicate_mask = df.duplicated(
        subset=["id"],
        keep="first"
    )

    duplicate_count = int(
        duplicate_mask.sum()
    )

    if duplicate_count > 0:

        print(
            f"  ⚠ Duplicate primary keys removed: "
            f"{duplicate_count}"
        )

        df = df[
            ~duplicate_mask
        ].copy()

    return df, duplicate_count


# ============================================================
# FOREIGN KEY VALIDATION
# ============================================================

def filter_invalid_foreign_keys(
    connection,
    df,
    table_name
):
    """
    Reject rows whose company_id is not present
    in the companies master table.
    """

    # companies is the parent table
    if table_name == "companies":
        return df, 0

    # Skip tables without company_id
    if "company_id" not in df.columns:
        return df, 0

    # Get valid master company IDs
    valid_company_ids = pd.read_sql_query(
        """
        SELECT id
        FROM companies;
        """,
        connection
    )["id"]

    valid_company_ids = set(
        valid_company_ids
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Normalize current DataFrame IDs
    company_ids = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Find invalid company IDs
    invalid_mask = (
        df["company_id"].notna()
        & ~company_ids.isin(
            valid_company_ids
        )
    )

    rejected_count = int(
        invalid_mask.sum()
    )

    if rejected_count > 0:

        invalid_ids = sorted(
            company_ids[
                invalid_mask
            ].unique()
        )

        print(
            f"  ⚠ FK-invalid rows rejected: "
            f"{rejected_count}"
        )

        print(
            f"  Invalid company IDs: "
            f"{invalid_ids}"
        )

    # Keep only valid rows
    valid_df = df[
        ~invalid_mask
    ].copy()

    return valid_df, rejected_count


# ============================================================
# DATA INSERTION
# ============================================================

def insert_dataframe(
    connection,
    df,
    table_name
):
    """
    Insert DataFrame rows into SQLite table.
    """

    if df.empty:
        return 0

    df.to_sql(
        table_name,
        connection,
        if_exists="append",
        index=False
    )

    return len(df)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Delete old database and create a fresh SQLite database
    using db/schema.sql.
    """

    DB_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not SCHEMA_FILE.exists():

        raise FileNotFoundError(
            f"Schema file not found: "
            f"{SCHEMA_FILE}"
        )

    # Remove previous database
    if DATABASE_FILE.exists():

        DATABASE_FILE.unlink()

        print(
            "🗑 Old database removed."
        )

    # Read schema
    with open(
        SCHEMA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        schema_sql = file.read()

    # Create connection
    connection = sqlite3.connect(
        DATABASE_FILE
    )

    # Enable foreign keys
    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )

    # Create tables
    connection.executescript(
        schema_sql
    )

    connection.commit()

    print(
        "✅ Clean database initialized."
    )

    return connection


# ============================================================
# FULL DATA LOAD
# ============================================================

def run_full_data_load():
    """
    Day 5:
    Load all 12 source files into SQLite,
    validate foreign keys,
    and generate load_audit.csv.
    """

    connection = None

    audit_records = []

    try:

        # -----------------------------------------------
        # Initialize clean database
        # -----------------------------------------------

        connection = initialize_database()

        print("\n" + "=" * 65)
        print("DAY 5 — FULL DATA LOAD")
        print("=" * 65)

        # -----------------------------------------------
        # Load all datasets
        # -----------------------------------------------

        for dataset in DATASETS:

            filename = dataset["file"]
            table_name = dataset["table"]
            header = dataset["header"]

            print("\n" + "-" * 65)

            print(
                f"Loading: {filename} "
                f"→ {table_name}"
            )

            print("-" * 65)

            source_rows = 0
            loaded_rows = 0
            rejected_rows = 0
            duplicate_rows = 0

            status = "SUCCESS"

            error_message = ""

            try:

                # =======================================
                # READ EXCEL
                # =======================================

                df = load_excel(
                    filename,
                    header
                )

                source_rows = len(df)

                print(
                    f"  Source rows: "
                    f"{source_rows}"
                )

                # =======================================
                # ALIGN WITH DATABASE SCHEMA
                # =======================================

                df = align_dataframe_to_table(
                    connection,
                    df,
                    table_name
                )

                # =======================================
                # REMOVE DUPLICATE PRIMARY KEYS
                # =======================================

                (
                    df,
                    duplicate_rows
                ) = remove_duplicate_primary_keys(
                    df,
                    table_name
                )

                # =======================================
                # FOREIGN KEY VALIDATION
                # =======================================

                (
                    df,
                    fk_rejected
                ) = filter_invalid_foreign_keys(
                    connection,
                    df,
                    table_name
                )

                rejected_rows += (
                    duplicate_rows
                )

                rejected_rows += (
                    fk_rejected
                )

                # =======================================
                # INSERT DATA
                # =======================================

                loaded_rows = insert_dataframe(
                    connection,
                    df,
                    table_name
                )

                connection.commit()

                print(
                    f"  ✅ Loaded rows: "
                    f"{loaded_rows}"
                )

                print(
                    f"  Rejected rows: "
                    f"{rejected_rows}"
                )

            except Exception as error:

                connection.rollback()

                status = "FAILED"

                error_message = str(error)

                loaded_rows = 0

                rejected_rows = (
                    source_rows
                )

                print(
                    f"  ❌ Load failed: "
                    f"{error}"
                )

            # ===========================================
            # AUDIT RECORD
            # ===========================================

            audit_records.append(
                {
                    "load_timestamp":
                        datetime.now().isoformat(
                            timespec="seconds"
                        ),

                    "source_file":
                        filename,

                    "table_name":
                        table_name,

                    "source_rows":
                        source_rows,

                    "loaded_rows":
                        loaded_rows,

                    "rejected_rows":
                        rejected_rows,

                    "duplicate_rows":
                        duplicate_rows,

                    "status":
                        status,

                    "error_message":
                        error_message,
                }
            )

        # =================================================
        # FOREIGN KEY CHECK
        # =================================================

        print("\n" + "=" * 65)
        print("FOREIGN KEY INTEGRITY CHECK")
        print("=" * 65)

        foreign_key_errors = (
            connection.execute(
                "PRAGMA foreign_key_check;"
            ).fetchall()
        )

        if not foreign_key_errors:

            print(
                "✅ PRAGMA foreign_key_check "
                "returned 0 rows."
            )

        else:

            print(
                f"❌ Foreign key violations found: "
                f"{len(foreign_key_errors)}"
            )

            for error in (
                foreign_key_errors[:10]
            ):

                print(error)

        # =================================================
        # FINAL DATABASE ROW COUNTS
        # =================================================

        print("\n" + "=" * 65)
        print("FINAL DATABASE ROW COUNTS")
        print("=" * 65)

        for dataset in DATASETS:

            table_name = dataset[
                "table"
            ]

            count = (
                connection.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {table_name};
                    """
                ).fetchone()[0]
            )

            print(
                f"{table_name}: {count}"
            )

    finally:

        # =================================================
        # SAVE LOAD AUDIT
        # =================================================

        OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        audit_df = pd.DataFrame(
            audit_records
        )

        audit_df.to_csv(
            AUDIT_FILE,
            index=False
        )

        print("\n" + "=" * 65)
        print("LOAD AUDIT REPORT")
        print("=" * 65)

        print(
            "✅ Load audit saved successfully"
        )

        print(
            f"File: {AUDIT_FILE}"
        )

        print(
            f"Tables audited: "
            f"{len(audit_df)}"
        )

        if connection is not None:
            connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    run_full_data_load()