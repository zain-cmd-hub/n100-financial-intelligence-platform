import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_screener_data

st.set_page_config(page_title="Capital Allocation", layout="wide")
st.title("Capital Allocation Map")

df = get_screener_data()
if df.empty:
    st.error("No financial data available.")
    st.stop()

# Ensure necessary columns are numeric
cols = [
    "free_cash_flow_cr",
    "capex_cr",
    "dividend_yield_pct",
    "financing_activity",
    "debt_to_equity",
    "revenue_cagr",
    "return_on_equity_pct",
    "asset_turnover",
    "net_profit_margin_pct",
    "market_cap_crore",
]

for c in cols:
    if c in df.columns:
        df[c] = pd.to_numeric(df[c].replace("Debt Free", 0), errors="coerce")


# Heuristic categorization of Capital Allocation Patterns (8 groups)
def categorize_allocation(row):
    """Handles operations for categorize_allocation."""
    fcf = row.get("free_cash_flow_cr", 0)
    capex = row.get("capex_cr", 0)
    div_yield = row.get("dividend_yield_pct", 0)
    fin_cf = row.get("financing_activity", 0)
    de = row.get("debt_to_equity", 0)
    rev_cagr = row.get("revenue_cagr", 0)
    roe = row.get("return_on_equity_pct", 0)
    ato = row.get("asset_turnover", 0)
    npm = row.get("net_profit_margin_pct", 0)

    # Fill NaNs with 0 for logic
    fcf = 0 if pd.isna(fcf) else fcf
    capex = 0 if pd.isna(capex) else capex
    div_yield = 0 if pd.isna(div_yield) else div_yield
    fin_cf = 0 if pd.isna(fin_cf) else fin_cf
    de = 0 if pd.isna(de) else de
    rev_cagr = 0 if pd.isna(rev_cagr) else rev_cagr
    roe = 0 if pd.isna(roe) else roe
    ato = 0 if pd.isna(ato) else ato
    npm = 0 if pd.isna(npm) else npm

    if fcf < 0 and npm < 0:
        return "Distressed / Turnaround"
    if ato > 1.5 and roe >= 15:
        return "Asset-Light Compounders"
    if fcf > 0 and rev_cagr > 10 and roe > 15:
        return "Consistent FCF Compounders"
    if de > 1.0 and rev_cagr > 10:
        return "Debt-Fueled Growth"
    if fin_cf < 0 and fcf > 0 and de > 0.5:
        return "Debt Reducers"
    if div_yield >= 2.0 and fcf > 0:
        return "Dividend Kings"
    if capex > fcf and capex > 0:
        return "Aggressive Reinvestors"
    if fcf > 0 and div_yield < 1.0 and capex < (fcf * 0.5):
        return "Cash Hoarders"

    return "Balanced / Other"


df["Allocation Pattern"] = df.apply(categorize_allocation, axis=1)

# Ensure market_cap_crore is valid for treemap sizing
df["market_cap_crore"] = df["market_cap_crore"].fillna(100)
df["market_cap_crore"] = df["market_cap_crore"].clip(lower=1)  # Treemap requires > 0

st.markdown("### Treemap of All 92 Companies by Capital Allocation Strategy")
st.caption(
    "Size represents Market Cap. Click on a pattern to expand/zoom in Plotly, or use the dropdown below for details."
)

fig = px.treemap(
    df,
    path=[px.Constant("Nifty 100"), "Allocation Pattern", "company_name_company"],
    values="market_cap_crore",
    color="Allocation Pattern",
    hover_data=[
        "free_cash_flow_cr",
        "capex_cr",
        "return_on_equity_pct",
        "dividend_yield_pct",
    ],
    height=700,
)
fig.update_traces(root_color="lightgrey")
fig.update_layout(margin={"t": 50, "l": 25, "r": 25, "b": 25})

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("Drill-down: Companies by Pattern")

patterns = sorted(df["Allocation Pattern"].unique().tolist())
selected_pattern = st.selectbox("Select a Pattern to view companies:", options=patterns)

filtered_df = df[df["Allocation Pattern"] == selected_pattern].copy()
display_cols = [
    "company_id",
    "company_name_company",
    "broad_sector",
    "market_cap_crore",
    "free_cash_flow_cr",
    "capex_cr",
    "dividend_yield_pct",
    "return_on_equity_pct",
]
display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()

display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name_company": "Company Name",
        "broad_sector": "Sector",
        "market_cap_crore": "Market Cap (Cr)",
        "free_cash_flow_cr": "FCF (Cr)",
        "capex_cr": "Capex (Cr)",
        "dividend_yield_pct": "Div Yield (%)",
        "return_on_equity_pct": "ROE (%)",
    }
)

st.dataframe(display_df.round(2), hide_index=True, use_container_width=True)
