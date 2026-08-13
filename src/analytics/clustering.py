import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_screener_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def run_clustering():
    """Handles operations for run_clustering."""
    df = get_screener_data()
    if df.empty:
        logger.error("No data found!")
        return

    features = {
        "return_on_equity_pct": "return_on_equity_pct",
        "debt_to_equity": "debt_to_equity",
        "revenue_cagr_5yr": "revenue_cagr",
        "fcf_cagr_5yr": "free_cash_flow_cagr",
        "operating_profit_margin_pct": "opm_percentage",
    }

    # Ensure all features exist in dataframe, fill with NaN if missing
    for col in features.values():
        if col not in df.columns:
            logger.warning(f"Column {col} not found, adding as NaN")
            df[col] = np.nan

    # Impute missing values with sector median for each metric
    df_imputed = df.copy()
    for col in features.values():
        df_imputed[col] = pd.to_numeric(df_imputed[col], errors="coerce")
        # Fill missing with broad_sector median
        df_imputed[col] = df_imputed.groupby("broad_sector")[col].transform(
            lambda x: x.fillna(x.median())
        )
        # If any still missing (e.g., whole sector missing), fill with overall median
        df_imputed[col] = df_imputed[col].fillna(df_imputed[col].median())
        df_imputed[col] = df_imputed[col].fillna(0)  # Ultimate fallback

    X = df_imputed[list(features.values())].values

    # StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Generate Elbow plot
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, marker="o", linestyle="--", color="b")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("Elbow Plot for KMeans Clustering")
    plt.xticks(K_range)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "elbow_plot.png")
    plt.close()

    # Run KMeans with k=5
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_ids = kmeans.fit_predict(X_scaled)

    # Calculate distance from centroid
    centroids = kmeans.cluster_centers_
    distances = np.linalg.norm(X_scaled - centroids[cluster_ids], axis=1)

    df["cluster_id"] = cluster_ids
    df["cluster_name"] = "TBD"
    df["distance_from_centroid"] = distances

    # Save output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_df = df[
        ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    ]
    output_path = OUTPUT_DIR / "cluster_labels.csv"
    output_df.to_csv(output_path, index=False)

    logger.info(
        f"Clustering complete. Generated {output_path} and {REPORTS_DIR}/elbow_plot.png"
    )


if __name__ == "__main__":
    run_clustering()
