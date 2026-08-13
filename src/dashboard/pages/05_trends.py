import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_full_trends_data

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Trend Analysis")

companies = get_companies()
if companies.empty:
    st.error("No companies data available.")
    st.stop()

# Prepare search box data
companies["search_key"] = companies["id"] + " - " + companies["company_name"]
search_keys = companies["search_key"].tolist()

selected_key = st.selectbox(
    "Search by Ticker or Company Name", options=[""] + search_keys, index=0
)

if not selected_key:
    st.info("Please select a company to view its historical trends.")
    st.stop()

ticker = selected_key.split(" - ")[0]
st.subheader(f"10-Year Historical Trends: {ticker}")

trends_df = get_full_trends_data(ticker)

if trends_df.empty:
    st.warning("No historical trend data found for this company.")
    st.stop()

available_metrics = [c for c in trends_df.columns if c != "year"]

# Multi-metric selector (up to 3)
selected_metrics = st.multiselect(
    "Select up to 3 metrics to overlay:",
    options=available_metrics,
    default=(
        ["Revenue", "Net Profit"]
        if "Revenue" in available_metrics
        else available_metrics[:2]
    ),
    max_selections=3,
)

if not selected_metrics:
    st.warning("Please select at least one metric to plot.")
    st.stop()

fig = go.Figure()

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

for i, metric in enumerate(selected_metrics):
    # Calculate YoY % change for annotations
    yoy_pct = trends_df[metric].pct_change() * 100

    text_annotations = []
    for val in yoy_pct:
        if pd.isna(val):
            text_annotations.append("")
        else:
            sign = "+" if val > 0 else ""
            text_annotations.append(f"{sign}{val:.1f}%")

    fig.add_trace(
        go.Scatter(
            x=trends_df["year"],
            y=trends_df[metric],
            mode="lines+markers+text",
            name=metric,
            text=text_annotations,
            textposition="top center",
            line={"width": 3, "color": colors[i]},
            marker={"size": 8},
        )
    )

fig.update_layout(
    title="Historical Metric Trends with YoY % Change",
    xaxis_title="Financial Year",
    yaxis_title="Value",
    hovermode="x unified",
    height=600,
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("Show Raw Data"):
    st.dataframe(trends_df, hide_index=True, use_container_width=True)
