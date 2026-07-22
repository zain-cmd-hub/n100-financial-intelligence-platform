import logging
from pathlib import Path
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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

PEER_GROUPS_FILE = BASE_DIR / "data" / "raw" / "peer_groups.xlsx"
OUTPUT_DIR = BASE_DIR / "reports" / "radar_charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AXES = {
    "return_on_equity_pct": "ROE",
    "roce_percentage": "ROCE",
    "net_profit_margin_pct": "NPM",
    "debt_to_equity": "D/E (Inv)",
    "free_cash_flow_cr": "FCF Score",
    "pat_cagr": "PAT CAGR 5yr",
    "revenue_cagr": "Revenue CAGR 5yr",
    "composite_score": "Composite Score"
}


def create_radar_chart(company_id, company_name, peer_group, company_values, peer_averages, labels):
    """
    Generate and save a radar chart for a company.
    """
    # Number of variables
    N = len(labels)
    
    # Angles for the radar chart
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    company_values = list(company_values) + [company_values[0]]
    peer_averages = list(peer_averages) + [peer_averages[0]]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Draw one axe per variable and add labels
    plt.xticks(angles[:-1], labels, color='grey', size=10)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([0.25, 0.5, 0.75, 1.0], ["25th", "50th", "75th", "100th"], color="grey", size=8)
    plt.ylim(0, 1.0)
    
    # Plot company
    ax.plot(angles, company_values, linewidth=2, linestyle='solid', label=company_name, color='#1f77b4')
    ax.fill(angles, company_values, '#1f77b4', alpha=0.25)
    
    # Plot peer average
    peer_label = f"Peer Avg: {peer_group}" if peer_group else "Nifty100 Avg"
    ax.plot(angles, peer_averages, linewidth=2, linestyle='dashed', label=peer_label, color='#ff7f0e')
    
    plt.title(f"{company_id} - Financial Radar\n", size=15, color='black', y=1.08)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Save
    out_file = OUTPUT_DIR / f"{company_id}_radar.png"
    plt.savefig(out_file, bbox_inches='tight', dpi=150)
    plt.close()


def generate_charts():
    logger.info("Starting Radar Chart Generation...")
    
    with ScreenerEngine() as engine:
        df = engine.merge_data()
        if df.empty:
            logger.error("Failed to load financial data.")
            return
            
        df = df.dropna(subset=["company_id"]).copy()
        
        # Scorer
        scorer = CompositeScorer(df)
        df = scorer.calculate_score()
        
    for col in AXES.keys():
        if col not in df.columns:
            logger.warning(f"Missing column {col}, filling with NaN")
            df[col] = np.nan
        else:
            if df[col].dtype == object:
                if col == "debt_to_equity":
                    df[col] = df[col].replace({"Debt Free": 0})
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    # Load Peer Groups
    try:
        peers_df = pd.read_excel(PEER_GROUPS_FILE)
        peers_df = peers_df[["company_id", "peer_group_name"]].drop_duplicates()
        df = df.merge(peers_df, on="company_id", how="left")
    except Exception as e:
        logger.error(f"Failed to read peer groups: {e}")
        df["peer_group_name"] = np.nan
        
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    
    # Calculate Ranks
    for col in AXES.keys():
        rank = df.groupby(["peer_group_name", "year"])[col].rank(pct=True, ascending=True, na_option='bottom')
        
        if col == "debt_to_equity":
            rank = 1.0 - rank
            
        # For companies with no peer group, calculate global rank
        global_rank = df.groupby(["year"])[col].rank(pct=True, ascending=True, na_option='bottom')
        if col == "debt_to_equity":
            global_rank = 1.0 - global_rank
            
        rank = rank.fillna(global_rank)
        rank = rank.clip(lower=0.0, upper=1.0)
        df[f"{col}_pct"] = rank

    # Calculate peer averages
    avg_cols = [f"{col}_pct" for col in AXES.keys()]
    peer_averages = df.groupby("peer_group_name")[avg_cols].mean().to_dict('index')
    
    nifty_avg = df[avg_cols].mean().to_dict()
    labels = list(AXES.values())
    
    # Take latest year for each company
    latest_df = df.sort_values("year").groupby("company_id").last().reset_index()
    
    count = 0
    for _, row in latest_df.iterrows():
        comp_id = str(row["company_id"])
        comp_name = str(row.get("company_name", comp_id))
        if pd.isna(row.get("company_name")):
            comp_name = comp_id

        peer_group = row["peer_group_name"]
        
        comp_vals = [row.get(f"{col}_pct", 0.0) for col in AXES.keys()]
        comp_vals = [0.0 if pd.isna(v) else v for v in comp_vals]
        
        if pd.isna(peer_group):
            peer_group = None
            avg_vals = [nifty_avg.get(f"{col}_pct", 0.5) for col in AXES.keys()]
        else:
            p_dict = peer_averages.get(peer_group, {})
            avg_vals = [p_dict.get(f"{col}_pct", 0.5) for col in AXES.keys()]
            
        create_radar_chart(comp_id, comp_name, peer_group, comp_vals, avg_vals, labels)
        count += 1
        
    logger.info(f"Generated {count} radar charts in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_charts()
