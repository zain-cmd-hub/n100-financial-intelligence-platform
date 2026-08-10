import os
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_screener_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'output'
REPORTS_DIR = Path(__file__).resolve().parents[2] / 'reports'

def run_profiling():
    # 1. Load data
    cluster_file = OUTPUT_DIR / 'cluster_labels.csv'
    if not cluster_file.exists():
        logger.error(f"Cluster file not found: {cluster_file}")
        return
        
    df_labels = pd.read_csv(cluster_file)
    df_screener = get_screener_data()
    
    # KPIs for correlation and stats
    core_kpis = [
        'return_on_equity_pct', 'roce_percentage', 'debt_to_equity', 
        'pe_ratio', 'pb_ratio', 'revenue_cagr', 'pat_cagr', 
        'free_cash_flow_cagr', 'opm_percentage', 'net_profit_margin_pct'
    ]
    
    # Missing columns handling
    for col in core_kpis:
        if col not in df_screener.columns:
            df_screener[col] = np.nan
            
    df = df_labels.merge(df_screener, on='company_id', how='left')
    
    # 2. Cluster Profiling & Naming
    cluster_features = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr', 'free_cash_flow_cagr', 'opm_percentage']
    
    # Convert features to numeric
    for col in cluster_features:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    profile = df.groupby('cluster_id')[cluster_features].median().fillna(0)
    
    # Dynamically assign names based on profile
    names = {}
    remaining_clusters = set(profile.index)
    
    def assign_max(col, name):
        if not remaining_clusters: return
        valid_idx = [i for i in remaining_clusters]
        best = max(valid_idx, key=lambda i: profile.loc[i, col])
        names[best] = name
        remaining_clusters.remove(best)
        
    assign_max('return_on_equity_pct', 'High-Quality Compounders')
    assign_max('revenue_cagr', 'Emerging Growth')
    assign_max('debt_to_equity', 'Distressed or Turnaround')
    assign_max('free_cash_flow_cagr', 'Defensive Dividend Payers')
    
    if remaining_clusters:
        for c in remaining_clusters:
            names[c] = 'Value Cyclicals'
            
    df_labels['cluster_name'] = df_labels['cluster_id'].map(names)
    df_labels.to_csv(cluster_file, index=False)
    logger.info(f"Updated {cluster_file} with cluster names")
    
    # 3. Correlation Heatmap
    corr_df = df[core_kpis].apply(pd.to_numeric, errors='coerce').corr(method='pearson')
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5)
    plt.title('Correlation Heatmap of 10 Core KPIs')
    plt.tight_layout()
    heatmap_path = REPORTS_DIR / 'correlation_heatmap.png'
    plt.savefig(heatmap_path)
    plt.close()
    logger.info(f"Generated {heatmap_path}")
    
    # 4. Outlier Detection (Z-score > 3 per broad_sector)
    outliers_list = []
    for sector, group in df.groupby('broad_sector'):
        for col in core_kpis:
            col_data = pd.to_numeric(group[col], errors='coerce').dropna()
            if len(col_data) > 1:
                z_scores = (col_data - col_data.mean()) / (col_data.std() + 1e-9)
                outlier_idx = z_scores[z_scores.abs() > 3].index
                for idx in outlier_idx:
                    outliers_list.append({
                        'company_id': group.loc[idx, 'company_id'],
                        'broad_sector': sector,
                        'metric': col,
                        'value': group.loc[idx, col],
                        'z_score': z_scores.loc[idx]
                    })
                    
    df_outliers = pd.DataFrame(outliers_list)
    outlier_path = OUTPUT_DIR / 'outlier_report.csv'
    if not df_outliers.empty:
        df_outliers = df_outliers[['company_id', 'broad_sector', 'metric', 'value', 'z_score']]
    df_outliers.to_csv(outlier_path, index=False)
    logger.info(f"Generated {outlier_path} with {len(df_outliers)} anomalies")
    
    # 5. Portfolio Stats (P10 to P90, Mean, Std)
    stats_list = []
    for col in core_kpis:
        col_data = pd.to_numeric(df[col], errors='coerce').dropna()
        if not col_data.empty:
            stats_list.append({
                'KPI': col,
                'P10': np.percentile(col_data, 10),
                'P25': np.percentile(col_data, 25),
                'P50': np.percentile(col_data, 50),
                'P75': np.percentile(col_data, 75),
                'P90': np.percentile(col_data, 90),
                'Mean': col_data.mean(),
                'Std': col_data.std()
            })
            
    df_stats = pd.DataFrame(stats_list)
    stats_path = OUTPUT_DIR / 'portfolio_stats.csv'
    df_stats.to_csv(stats_path, index=False)
    logger.info(f"Generated {stats_path}")

if __name__ == "__main__":
    run_profiling()
