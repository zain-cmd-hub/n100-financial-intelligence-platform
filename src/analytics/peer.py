import logging
import sqlite3
import warnings
from pathlib import Path

import pandas as pd
import numpy as np

# Suppress specific pandas warnings if necessary
warnings.simplefilter(action='ignore', category=FutureWarning)

import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

try:
    from src.screener.engine import ScreenerEngine
    from src.screener.scoring import CompositeScorer
except ImportError:
    from engine import ScreenerEngine
    from scoring import CompositeScorer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"
PEER_GROUPS_FILE = BASE_DIR / "data" / "raw" / "peer_groups.xlsx"

METRICS_TO_RANK = {
    "return_on_equity_pct": "ROE",
    "roce_percentage": "ROCE",
    "net_profit_margin_pct": "Net Profit Margin",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF",
    "pat_cagr": "PAT CAGR 5yr",
    "revenue_cagr": "Revenue CAGR 5yr",
    "eps_cagr": "EPS CAGR 5yr",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover"
}


def compute_peer_percentiles():
    logger.info("Starting Peer Percentile Ranking Engine...")

    if not PEER_GROUPS_FILE.exists():
        logger.error(f"Peer groups file not found: {PEER_GROUPS_FILE}")
        return

    # 1. Load Financial Data
    with ScreenerEngine() as engine:
        df = engine.merge_data()
        if df.empty:
            logger.error("Failed to load financial data.")
            return
            
        # Drop companies with invalid/empty company_id
        df = df.dropna(subset=["company_id"]).copy()

        # Generate CAGR metrics by applying scoring engine
        scorer = CompositeScorer(df)
        df = scorer.calculate_score()

    # Clean numeric columns before ranking
    for col in METRICS_TO_RANK.keys():
        if col in df.columns:
            # Handle string artifacts like "Debt Free" for interest_coverage and debt_to_equity
            if df[col].dtype == object:
                # E.g., 'Debt Free' in debt_to_equity -> 0, interest_coverage -> 999999
                if col == "debt_to_equity":
                    df[col] = df[col].replace({"Debt Free": 0})
                elif col == "interest_coverage":
                    df[col] = df[col].replace({"Debt Free": 999999})
            
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            logger.warning(f"Metric column missing in dataframe: {col}")
            df[col] = np.nan

    # 2. Load Peer Groups
    try:
        peers_df = pd.read_excel(PEER_GROUPS_FILE)
    except Exception as e:
        logger.error(f"Failed to read peer groups file: {e}")
        return
        
    if "company_id" not in peers_df.columns or "peer_group_name" not in peers_df.columns:
        logger.error("peer_groups.xlsx must contain 'company_id' and 'peer_group_name' columns.")
        return

    peers_df = peers_df[["company_id", "peer_group_name"]].drop_duplicates()

    # 3. Merge and Check for unassigned companies
    merged_df = df.merge(peers_df, on="company_id", how="left")

    unassigned_mask = merged_df["peer_group_name"].isna()
    if unassigned_mask.any():
        unassigned_companies = merged_df.loc[unassigned_mask, "company_id"].unique()
        for company in unassigned_companies:
            logger.warning(f"No peer group assigned: {company}")

    # Remove unassigned for ranking
    rank_df = merged_df[~unassigned_mask].copy()

    # 4. Compute PERCENT_RANK
    # We rank within each peer group AND year to compare companies fairly in the same timeframe
    rank_df["year"] = pd.to_numeric(rank_df["year"], errors="coerce").fillna(0).astype(int)
    
    group_cols = ["peer_group_name", "year"]
    
    melted_rows = []

    for internal_col, display_name in METRICS_TO_RANK.items():
        if internal_col not in rank_df.columns:
            continue
            
        # Calculate rank: default handles NaNs automatically usually, but we drop na for precise ranking
        # rank(pct=True) computes PERCENT_RANK
        rank_series = rank_df.groupby(group_cols)[internal_col].rank(pct=True, ascending=True, na_option='bottom')
        
        # Invert rank for D/E (lower is better)
        if internal_col == "debt_to_equity":
            # For debt to equity, we want lower values to have higher ranks
            # However, `rank(ascending=True)` gives lower values a smaller percentile.
            # E.g. Lowest D/E -> 10th percentile. We want it to be 90th percentile.
            rank_series = 1.0 - rank_series

        temp_df = rank_df[["company_id", "peer_group_name", "year", internal_col]].copy()
        temp_df.rename(columns={internal_col: "value"}, inplace=True)
        temp_df["metric"] = display_name
        temp_df["percentile_rank"] = rank_series
        
        # Drop rows where the value was NaN as they shouldn't realistically be ranked
        temp_df = temp_df.dropna(subset=["value"])
        
        melted_rows.append(temp_df)

    if not melted_rows:
        logger.error("No metrics could be ranked.")
        return

    final_df = pd.concat(melted_rows, ignore_index=True)
    
    # Reorder columns as requested
    final_df = final_df[["company_id", "peer_group_name", "metric", "value", "percentile_rank", "year"]]

    # 5. Write to SQLite
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        final_df.to_sql("peer_percentiles", conn, if_exists="replace", index=False)
        conn.close()
        logger.info(f"Successfully populated peer_percentiles table with {len(final_df)} records.")
    except sqlite3.Error as e:
        logger.error(f"Failed to write to database: {e}")

if __name__ == "__main__":
    compute_peer_percentiles()
