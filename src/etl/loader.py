from pathlib import Path
import sqlite3
import pandas as pd

from normaliser import normalize_ticker, normalize_year


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA = BASE_DIR / "data" / "raw"

DB_DIR = BASE_DIR / "db"
SCHEMA_FILE = DB_DIR / "schema.sql"
DATABASE_FILE = DB_DIR / "nifty100.db"


# ============================================================
# EXCEL FILE LOADER
# ============================================================

def load_excel(file_path, header=0):
    """
    Load an Excel file safely.
    """

    try:
        df = pd.read_excel(file_path, header=header)

        print(f"Loaded: {Path(file_path).name}")
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")

        return df

    except Exception as e:
        print(f"❌ Error loading {file_path}: {e}")
        return None


# ============================================================
# LOAD ALL 12 SOURCE FILES
# ============================================================

def load_all_files():
    """
    Load all 12 datasets from data/raw.

    Core datasets use header=1.
    Supplementary datasets use header=0.
    """

    datasets = {
        # Core datasets
        "companies.xlsx": 1,
        "profitandloss.xlsx": 1,
        "balancesheet.xlsx": 1,
        "cashflow.xlsx": 1,
        "analysis.xlsx": 1,
        "documents.xlsx": 1,
        "prosandcons.xlsx": 1,

        # Supplementary datasets
        "financial_ratios.xlsx": 0,
        "market_cap.xlsx": 0,
        "peer_groups.xlsx": 0,
        "sectors.xlsx": 0,
        "stock_prices.xlsx": 0,
    }

    loaded_data = {}

    for filename, header in datasets.items():

        file_path = RAW_DATA / filename

        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            continue

        df = load_excel(file_path, header)

        if df is not None:
            loaded_data[filename] = df

    return loaded_data


# ============================================================
# INITIALIZE SQLITE DATABASE
# ============================================================

def initialize_database():
    """
    Create the SQLite database and initialize all tables
    using db/schema.sql.
    """

    # Ensure db directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Check schema file
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    # Read SQL schema
    with open(SCHEMA_FILE, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    # Connect to SQLite database
    connection = sqlite3.connect(DATABASE_FILE)

    try:
        # Enable foreign key enforcement
        connection.execute("PRAGMA foreign_keys = ON;")

        # Execute complete schema
        connection.executescript(schema_sql)

        # Save changes
        connection.commit()

        # Check foreign key status
        foreign_keys_status = connection.execute(
            "PRAGMA foreign_keys;"
        ).fetchone()[0]

        # Get all created tables
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
            """
        ).fetchall()

        print("\n" + "=" * 60)
        print("✅ DATABASE INITIALIZATION SUCCESSFUL")
        print("=" * 60)

        print(f"Database File: {DATABASE_FILE}")
        print(
            f"Foreign Keys Enabled: "
            f"{'YES' if foreign_keys_status == 1 else 'NO'}"
        )

        print(f"Tables Created: {len(tables)}")

        print("\nDatabase Tables:")

        for number, table in enumerate(tables, start=1):
            print(f"{number}. {table[0]}")

        print("=" * 60)

        return True

    except sqlite3.Error as error:

        print("\n❌ DATABASE INITIALIZATION FAILED")
        print(f"SQLite Error: {error}")

        connection.rollback()

        return False

    finally:
        connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    initialize_database()