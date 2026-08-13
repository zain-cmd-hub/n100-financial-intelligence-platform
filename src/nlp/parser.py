import logging
import re
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


def parse_analysis_text():
    """Handles operations for parse_analysis_text."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Connect to DB and fetch analysis table
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        df_analysis = pd.read_sql("SELECT * FROM analysis", conn)
    except Exception as e:
        logger.error(f"Failed to read 'analysis' table: {e}")
        conn.close()
        return
    finally:
        conn.close()

    logger.info(f"Loaded {len(df_analysis)} rows from analysis table.")

    # Fields to parse
    target_fields = [
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]

    # Regex pattern: extracts period and value
    pattern = re.compile(r"(\d+)\s*Years?:?\s*(-?[\d.]+)%")

    parsed_records = []
    failed_records = []

    for _, row in df_analysis.iterrows():
        company_id = row.get("company_id")
        if not company_id or pd.isna(company_id):
            continue

        for field in target_fields:
            text_val = row.get(field)
            if pd.isna(text_val) or not str(text_val).strip():
                continue

            text_val = str(text_val).strip()

            # Use finditer to handle multiple lines in one cell if they exist,
            # though usually it might just be single match or split by newlines.
            # Let's split by newline to handle multiple records in one cell
            lines = [line.strip() for line in text_val.split("\n") if line.strip()]

            for line in lines:
                match = pattern.search(line)
                if match:
                    period_years = int(match.group(1))
                    value_pct = float(match.group(2))
                    parsed_records.append(
                        {
                            "company_id": company_id,
                            "metric_type": field,
                            "period_years": period_years,
                            "value_pct": value_pct,
                        }
                    )
                elif "TTM" not in line and "ttm" not in line.lower():
                    # If it's not TTM and didn't match pattern, log as failure
                    # We ignore TTM since the pattern is explicitly for Years
                    failed_records.append(
                        {
                            "company_id": company_id,
                            "metric_type": field,
                            "raw_text": line,
                        }
                    )

    # Save Parsed Results
    df_parsed = pd.DataFrame(parsed_records)
    parsed_path = OUTPUT_DIR / "analysis_parsed.csv"
    if not df_parsed.empty:
        df_parsed.to_csv(parsed_path, index=False)
        logger.info(f"Saved {len(df_parsed)} parsed records to {parsed_path}")
    else:
        logger.warning("No records parsed successfully.")

    # Save Failures
    df_failures = pd.DataFrame(failed_records)
    failures_path = OUTPUT_DIR / "parse_failures.csv"
    if not df_failures.empty:
        df_failures.to_csv(failures_path, index=False)
        logger.warning(f"Logged {len(df_failures)} parsing failures to {failures_path}")
    else:
        # Create empty file
        pd.DataFrame(columns=["company_id", "metric_type", "raw_text"]).to_csv(
            failures_path, index=False
        )
        logger.info("No parsing failures detected.")

    # 2. Cross-Validation
    logger.info("Starting cross-validation with Ratio Engine...")
    df_screener = get_screener_data()
    if df_screener.empty:
        logger.error("Failed to load screener data for cross-validation.")
        return

    # We only care about 5-year CAGR for cross validation per requirements
    df_screener = df_screener[["company_id", "revenue_cagr", "pat_cagr"]].copy()

    # Filter parsed records for 5 Years
    if not df_parsed.empty:
        df_parsed_5yr = df_parsed[df_parsed["period_years"] == 5]

        divergences = []

        # Merge parsed data with screener data
        for _, parsed_row in df_parsed_5yr.iterrows():
            cid = parsed_row["company_id"]
            metric = parsed_row["metric_type"]
            parsed_val = parsed_row["value_pct"]

            screener_row = df_screener[df_screener["company_id"] == cid]
            if screener_row.empty:
                continue

            screener_val = None
            if metric == "compounded_sales_growth":
                screener_val = screener_row["revenue_cagr"].values[0]
            elif metric == "compounded_profit_growth":
                screener_val = screener_row["pat_cagr"].values[0]

            if pd.notna(screener_val):
                diff = abs(parsed_val - screener_val)
                if diff > 5.0:
                    divergences.append(
                        {
                            "company_id": cid,
                            "metric_type": metric,
                            "parsed_value": parsed_val,
                            "computed_value": screener_val,
                            "difference": diff,
                        }
                    )

        div_path = OUTPUT_DIR / "divergence_flags.csv"
        if divergences:
            df_div = pd.DataFrame(divergences)
            df_div.to_csv(div_path, index=False)
            logger.warning(
                f"Found {len(df_div)} divergence flags > 5%. Saved to {div_path}"
            )
        else:
            pd.DataFrame(
                columns=[
                    "company_id",
                    "metric_type",
                    "parsed_value",
                    "computed_value",
                    "difference",
                ]
            ).to_csv(div_path, index=False)
            logger.info("No divergences > 5% found. Cross-validation successful.")


if __name__ == "__main__":
    parse_analysis_text()
