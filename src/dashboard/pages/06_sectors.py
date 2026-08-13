import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_screener_data

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Deep-Dive Analysis")

# Load data
df = get_screener_data()
if df.empty:
    st.error("No data available for sector analysis.")
    st.stop()

# Ensure necessary columns are numeric
num_cols = [
    "sales",
    "return_on_equity_pct",
    "market_cap_crore",
    "pe_ratio",
    "net_profit_margin_pct",
]
for c in num_cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c].replace("Debt Free", 0), errors="coerce")

# Get unique sectors
sectors = sorted(df["broad_sector"].dropna().unique().tolist())
if not sectors:
    st.error("No sector classifications found.")
    st.stop()

selected_sector = st.selectbox("Select a Sector to Analyze", options=sectors)
st.markdown("---")

sector_df = df[df["broad_sector"] == selected_sector].copy()
sector_df.dropna(
    subset=["sales", "return_on_equity_pct", "market_cap_crore"], inplace=True
)

if sector_df.empty:
    st.warning("Insufficient data to generate charts for this sector.")
    st.stop()

st.subheader(f"{selected_sector} Ecosystem: Revenue vs ROE")
st.caption("Bubble size indicates Market Capitalization. Color denotes Sub-sector.")

# Bubble Chart
fig_bubble = px.scatter(
    sector_df,
    x="sales",
    y="return_on_equity_pct",
    size="market_cap_crore",
    color="sub_sector",
    hover_name="company_name_company",
    hover_data={
        "sales": ":.2f",
        "return_on_equity_pct": ":.2f",
        "market_cap_crore": ":.2f",
    },
    labels={
        "sales": "Revenue (Cr)",
        "return_on_equity_pct": "ROE (%)",
        "market_cap_crore": "Market Cap (Cr)",
        "sub_sector": "Sub Sector",
    },
    size_max=60,
    height=600,
)

# Add gridlines and zero lines
fig_bubble.update_layout(
    xaxis={"showgrid": True, "zeroline": True, "zerolinecolor": "lightgrey"},
    yaxis={"showgrid": True, "zeroline": True, "zerolinecolor": "lightgrey"},
    hovermode="closest",
)
st.plotly_chart(fig_bubble, use_container_width=True)

st.markdown("---")
st.subheader("Sub-Sector Median KPIs")

# Group by sub-sector and calculate medians
kpi_df = (
    sector_df.groupby("sub_sector")[
        ["pe_ratio", "return_on_equity_pct", "net_profit_margin_pct"]
    ]
    .median()
    .reset_index()
)

# Reshape for grouped bar chart
kpi_melted = kpi_df.melt(
    id_vars="sub_sector", var_name="Metric", value_name="Median Value"
)
rename_metrics = {
    "pe_ratio": "Median P/E",
    "return_on_equity_pct": "Median ROE (%)",
    "net_profit_margin_pct": "Median NPM (%)",
}
kpi_melted["Metric"] = kpi_melted["Metric"].map(rename_metrics)

fig_bar = px.bar(
    kpi_melted,
    x="sub_sector",
    y="Median Value",
    color="Metric",
    barmode="group",
    text_auto=".2f",
    labels={"sub_sector": "Sub Sector"},
    height=500,
)

st.plotly_chart(fig_bar, use_container_width=True)

with st.expander("Show Raw Data"):
    st.dataframe(
        sector_df[
            [
                "company_id",
                "company_name_company",
                "sub_sector",
                "sales",
                "return_on_equity_pct",
                "market_cap_crore",
                "pe_ratio",
            ]
        ],
        hide_index=True,
        use_container_width=True,
    )
