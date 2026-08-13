import logging
import sqlite3
import sys
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_screener_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parents[2] / "db" / "nifty100.db"
OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def determine_pattern(cfo, cfi, cff):
    """Handles operations for determine_pattern."""
    if cfo >= 0 and cfi <= 0 and cff <= 0:
        return "Cash Cow / Self-Sustaining"
    elif cfo >= 0 and cfi <= 0 and cff > 0:
        return "Reinvestor"
    elif cfo >= 0 and cfi > 0 and cff <= 0:
        return "Deleveraging"
    elif cfo >= 0 and cfi > 0 and cff > 0:
        return "Cash Accumulator"
    elif cfo < 0 and cfi <= 0 and cff > 0:
        return "Distress Signal"
    elif cfo < 0 and cfi > 0 and cff > 0:
        return "Asset Seller"
    elif cfo < 0 and cfi > 0 and cff <= 0:
        return "Liquidating"
    elif cfo < 0 and cfi <= 0 and cff <= 0:
        return "High Risk / Bleeding"
    else:
        return "Unknown"


def generate_report():
    """Handles operations for generate_report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Reconstruct capital_allocation.csv (since it was missing)
    conn = sqlite3.connect(DB_PATH)
    try:
        cf_df = pd.read_sql("SELECT * FROM cashflow", conn)
    except Exception as e:
        logger.error(f"Failed to load cash_flow: {e}")
        conn.close()
        return
    finally:
        conn.close()

    df_screener = get_screener_data()
    valid_companies = df_screener["company_id"].unique()

    cf_df = cf_df[cf_df["company_id"].isin(valid_companies)]

    allocations = []

    for _, row in cf_df.iterrows():
        cfo = pd.to_numeric(row.get("operating_activity"), errors="coerce")
        cfi = pd.to_numeric(row.get("investing_activity"), errors="coerce")
        cff = pd.to_numeric(row.get("financing_activity"), errors="coerce")

        # handle nan
        cfo = 0 if pd.isna(cfo) else cfo
        cfi = 0 if pd.isna(cfi) else cfi
        cff = 0 if pd.isna(cff) else cff

        pattern = determine_pattern(cfo, cfi, cff)
        allocations.append(
            {"company_id": row["company_id"], "year": row["year"], "pattern": pattern}
        )

    df_alloc = pd.DataFrame(allocations)
    df_alloc.sort_values(by=["company_id", "year"], inplace=True)
    df_alloc.to_csv(OUTPUT_DIR / "capital_allocation.csv", index=False)
    logger.info(f"Reconstructed capital_allocation.csv with {len(df_alloc)} rows.")

    # 2. Distribution Summary for Latest Year
    latest_year = df_alloc["year"].max()
    latest_alloc = df_alloc[df_alloc["year"] == latest_year].copy()

    distribution = latest_alloc["pattern"].value_counts()
    print("--- Capital Allocation Distribution (Latest Year) ---")
    print(distribution)

    # 3. Add to cashflow_intelligence.xlsx
    cf_intel_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    if cf_intel_path.exists():
        df_intel = pd.read_excel(cf_intel_path)
        # We will merge the pattern replacing the existing capital_allocation_label if present
        if "capital_allocation_label" in df_intel.columns:
            df_intel.drop(columns=["capital_allocation_label"], inplace=True)

        # Join latest pattern
        latest_mapping = latest_alloc[["company_id", "pattern"]].rename(
            columns={"pattern": "capital_allocation_label"}
        )
        df_intel = pd.merge(df_intel, latest_mapping, on="company_id", how="left")

        df_intel.to_excel(cf_intel_path, index=False)
        logger.info(
            f"Updated {cf_intel_path.name} with true capital allocation labels."
        )
    else:
        logger.warning(f"{cf_intel_path.name} not found. Cannot update it.")

    # 4. YoY Pattern Changes Text Report / CSV
    changes = []

    for cid in valid_companies:
        comp_data = df_alloc[df_alloc["company_id"] == cid].sort_values(
            "year", ascending=True
        )
        if len(comp_data) >= 2:
            last_two = comp_data.tail(2)
            prev_pattern = last_two.iloc[0]["pattern"]
            curr_pattern = last_two.iloc[1]["pattern"]

            if prev_pattern != curr_pattern:
                changes.append(
                    {
                        "company_id": cid,
                        "previous_year_pattern": prev_pattern,
                        "latest_year_pattern": curr_pattern,
                        "change_summary": f"Moved from {prev_pattern} to {curr_pattern}",
                    }
                )

    df_changes = pd.DataFrame(changes)
    df_changes.to_csv(OUTPUT_DIR / "pattern_changes.csv", index=False)
    logger.info(
        f"Identified {len(df_changes)} YoY pattern changes. Saved to pattern_changes.csv."
    )


if __name__ == "__main__":
    generate_report()
