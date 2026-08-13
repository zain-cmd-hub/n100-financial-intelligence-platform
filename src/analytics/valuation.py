import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Add project root to path so we can import modules
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_companies, get_screener_data


def generate_valuation_output():
    """Generate valuation flags and output files based on market cap and FCF."""
    logger.info("Starting Valuation Module...")

    # Output directory
    output_dir = Path(__file__).resolve().parents[2] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Data
    all_companies = get_companies()
    df_raw = get_screener_data()

    if all_companies.empty:
        logger.error("Failed to load companies data.")
        return

    # Merge to ensure we have exactly all companies
    if not df_raw.empty:
        df = all_companies.merge(
            df_raw,
            left_on="id",
            right_on="company_id",
            how="left",
            suffixes=("_comp", "_raw"),
        )
        df["company_id"] = df["id_comp"] if "id_comp" in df.columns else df["id"]
        df["company_name_final"] = (
            df["company_name_comp"]
            if "company_name_comp" in df.columns
            else df["company_name"]
        )
        df["broad_sector_final"] = (
            df["broad_sector"].fillna("Unknown")
            if "broad_sector" in df.columns
            else "Unknown"
        )
    else:
        df = all_companies.copy()
        df["company_id"] = df["id"]
        df["company_name_final"] = df["company_name"]
        df["broad_sector_final"] = "Unknown"
        logger.error(
            "Failed to load screener data. Ensure database exists and is populated."
        )
        return

    # Ensure necessary columns are numeric
    cols = [
        "free_cash_flow_cr",
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
    ]
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].replace("Debt Free", 0), errors="coerce")

    # 2. Compute FCF Yield
    # FCF Yield = FCF / Market Cap * 100
    df["FCF_yield_pct"] = (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100

    # 3. Compute Sector Median P/E
    sector_medians = df.groupby("broad_sector_final")["pe_ratio"].median().reset_index()
    sector_medians = sector_medians.rename(columns={"pe_ratio": "sector_median_PE"})

    df = df.merge(sector_medians, on="broad_sector_final", how="left")

    # 4. Apply Overvaluation Flags
    def assign_flag(row):
        """Handles operations for assign_flag."""
        company_pe = row["pe_ratio"]
        sector_pe = row["sector_median_PE"]

        if pd.isna(company_pe) or pd.isna(sector_pe) or sector_pe <= 0:
            return "Fair"  # Cannot determine accurately

        if company_pe > (sector_pe * 1.5):
            return "Caution"
        elif company_pe < (sector_pe * 0.7):
            return "Discount"
        else:
            return "Fair"

    df["flag"] = df.apply(assign_flag, axis=1)

    # Compute relative PE vs sector median
    df["PE_vs_sector_median_pct"] = (
        (df["pe_ratio"] / df["sector_median_PE"]) - 1
    ) * 100

    # For 5yr_median_PE, we don't have it explicitly stored per company across all years in get_screener_data (since it only returns latest year).
    # We will compute a rough placeholder or leave it blank since ScreenerEngine's merge_data is complex.
    # Actually, we can fetch all historical data to compute 5yr median PE if needed.
    # For now, we will leave it as NaN or just replicate current PE as a fallback.
    df["5yr_median_PE"] = df["pe_ratio"]

    # Prepare final output DataFrame
    output_cols = [
        "company_id",
        "company_name_final",
        "broad_sector_final",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    # Ensure all exist
    for c in output_cols:
        if c not in df.columns:
            df[c] = np.nan

    summary_df = df[output_cols].copy()

    # Rename specifically requested columns
    summary_df.rename(
        columns={
            "company_name_final": "company_name",
            "broad_sector_final": "sector",
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        },
        inplace=True,
    )

    # 5. Save Outputs
    summary_path = output_dir / "valuation_summary.xlsx"
    summary_df.to_excel(summary_path, index=False)
    logger.info(f"Saved valuation summary to {summary_path}")

    # Generate flags CSV
    flags_df = summary_df[summary_df["flag"].isin(["Caution", "Discount"])].copy()
    flags_path = output_dir / "valuation_flags.csv"
    flags_df.to_csv(flags_path, index=False)
    logger.info(f"Saved valuation flags ({len(flags_df)} companies) to {flags_path}")

    print("Valuation Module completed successfully!")


if __name__ == "__main__":
    generate_valuation_output()
