import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import (
    get_companies,
    get_peer_group_names,
    get_peers,
    get_screener_data,
)

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Peer Comparison & Benchmarking")

# Load base data
group_names = get_peer_group_names()
if not group_names:
    st.error("No peer groups found in the database.")
    st.stop()

# 1. Peer Group Selection
selected_group = st.selectbox("Select Peer Group", options=group_names)

peers_df = get_peers(selected_group)
if peers_df.empty:
    st.warning("No companies found in this peer group.")
    st.stop()

# Get the list of company_ids in this group
peer_tickers = peers_df["company_id"].tolist()

# Find the default benchmark (is_benchmark == 1)
default_benchmark = (
    peers_df[peers_df["is_benchmark"] == 1]["company_id"].iloc[0]
    if 1 in peers_df["is_benchmark"].values
    else peer_tickers[0]
)

benchmark_company = st.selectbox(
    "Select Benchmark Company",
    options=peer_tickers,
    index=peer_tickers.index(default_benchmark),
)

# Load all metrics for the companies in this peer group
screener_df = get_screener_data()
companies_df = get_companies()

if screener_df.empty or companies_df.empty:
    st.error("Financial data not available.")
    st.stop()

# Filter for the peer group
group_data = screener_df[screener_df["company_id"].isin(peer_tickers)].copy()
group_companies = companies_df[companies_df["id"].isin(peer_tickers)].copy()

# Merge ROCE and Company Name
group_data = group_data.merge(
    group_companies[["id", "roce_percentage", "company_name"]],
    left_on="company_id",
    right_on="id",
    how="left",
)

# 2. Side-by-side KPI Table
st.subheader(f"KPI Comparison: {selected_group}")
table_cols = [
    "company_id",
    "company_name",
    "return_on_equity_pct",
    "roce_percentage",
    "pe_ratio",
    "pb_ratio",
    "revenue_cagr",
]

# Ensure columns exist
for c in table_cols:
    if c not in group_data.columns:
        group_data[c] = None

compare_df = group_data[table_cols].copy()
compare_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company Name",
        "return_on_equity_pct": "ROE (%)",
        "roce_percentage": "ROCE (%)",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "revenue_cagr": "Rev CAGR (%)",
    },
    inplace=True,
)

# Clean numeric for styling
numeric_display = ["ROE (%)", "ROCE (%)", "P/E", "P/B", "Rev CAGR (%)"]
for c in numeric_display:
    compare_df[c] = pd.to_numeric(compare_df[c], errors="coerce")


# Style the dataframe
def highlight_benchmark(row):
    """Handles operations for highlight_benchmark."""
    color = (
        "background-color: rgba(255, 215, 0, 0.2)"
        if row["Ticker"] == benchmark_company
        else ""
    )
    return [color] * len(row)


styled_df = compare_df.style.apply(highlight_benchmark, axis=1)
# Highlight best metrics (Max for returns, Min for valuation)
styled_df = styled_df.highlight_max(
    subset=["ROE (%)", "ROCE (%)", "Rev CAGR (%)"], color="rgba(0, 255, 0, 0.2)"
)
styled_df = styled_df.highlight_min(subset=["P/E", "P/B"], color="rgba(0, 255, 0, 0.2)")

st.dataframe(styled_df.format(precision=2), hide_index=True, use_container_width=True)

# 3. Radar Chart
st.markdown("---")
st.subheader(f"Radar Analysis: {benchmark_company} vs Group Average")

# Select 8 metrics for Radar
radar_metrics = [
    "return_on_equity_pct",
    "roce_percentage",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "revenue_cagr",
    "pat_cagr",
    "pe_ratio",
    "pb_ratio",
]
radar_labels = [
    "ROE",
    "ROCE",
    "OPM",
    "NPM",
    "Rev CAGR",
    "PAT CAGR",
    "P/E (Inv)",
    "P/B (Inv)",
]

# We need to normalize these 8 metrics to 0-100 scale for a proper radar chart.
# Note: For P/E and P/B, lower is better, so we invert them.
radar_df = group_data[["company_id"] + radar_metrics].copy()

# Convert all to numeric
for c in radar_metrics:
    radar_df[c] = pd.to_numeric(radar_df[c], errors="coerce").fillna(0)

# Calculate group averages
group_avg = radar_df[radar_metrics].mean()
bench_data = radar_df[radar_df["company_id"] == benchmark_company][radar_metrics].iloc[
    0
]

# Normalize function mapping min->0, max->100
normalized_bench = []
normalized_avg = []

for i, col in enumerate(radar_metrics):
    col_min = radar_df[col].min()
    col_max = radar_df[col].max()

    # Avoid division by zero
    if col_max == col_min:
        n_bench = 50
        n_avg = 50
    else:
        # Invert logic for PE and PB
        if col in ["pe_ratio", "pb_ratio"]:
            n_bench = 100 - ((bench_data[col] - col_min) / (col_max - col_min) * 100)
            n_avg = 100 - ((group_avg[col] - col_min) / (col_max - col_min) * 100)
        else:
            n_bench = (bench_data[col] - col_min) / (col_max - col_min) * 100
            n_avg = (group_avg[col] - col_min) / (col_max - col_min) * 100

    normalized_bench.append(n_bench)
    normalized_avg.append(n_avg)

# Plotly Radar Chart
fig = go.Figure()
fig.add_trace(
    go.Scatterpolar(
        r=normalized_bench,
        theta=radar_labels,
        fill="toself",
        name=benchmark_company,
        line_color="blue",
    )
)
fig.add_trace(
    go.Scatterpolar(
        r=normalized_avg,
        theta=radar_labels,
        fill="toself",
        name="Group Average",
        line_color="orange",
    )
)

fig.update_layout(
    polar={"radialaxis": {"visible": True, "range": [0, 100]}}, showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "Note: Metrics are normalized to a 0-100 scale for visualization. For Valuation metrics (P/E, P/B), a higher score indicates a more attractive (lower) valuation."
)
