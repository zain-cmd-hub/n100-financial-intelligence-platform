import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_screener_data

st.set_page_config(page_title="Screener", layout="wide")
st.title("Advanced Stock Screener")

df = get_screener_data()
if df.empty:
    st.error("No screener data available.")
    st.stop()

# Initialize session state for sliders
slider_keys = {
    "roe_min": 0.0,
    "de_max": 5.0,
    "fcf_min": -10000.0,
    "rev_cagr_min": -50.0,
    "pat_cagr_min": -50.0,
    "opm_min": -50.0,
    "pe_max": 200.0,
    "pb_max": 50.0,
    "div_yield_min": 0.0,
    "icr_min": -10.0,
}
for key, default_val in slider_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_val


# Preset Logic
def apply_preset(preset):
    """Handles operations for apply_preset."""
    # Reset to defaults first
    for k, v in slider_keys.items():
        st.session_state[k] = v

    if preset == "Quality":
        st.session_state["roe_min"] = 15.0
        st.session_state["de_max"] = 1.0
        st.session_state["fcf_min"] = 0.0
        st.session_state["rev_cagr_min"] = 10.0
    elif preset == "Value":
        st.session_state["pe_max"] = 20.0
        st.session_state["pb_max"] = 2.0
        st.session_state["div_yield_min"] = 1.0
        st.session_state["de_max"] = 1.0
    elif preset == "Growth":
        st.session_state["rev_cagr_min"] = 15.0
        st.session_state["pat_cagr_min"] = 15.0
        st.session_state["roe_min"] = 10.0
    elif preset == "Dividend":
        st.session_state["div_yield_min"] = 3.0
        st.session_state["fcf_min"] = 0.0
        st.session_state["de_max"] = 1.0
    elif preset == "Debt-Free":
        st.session_state["de_max"] = 0.1
        st.session_state["icr_min"] = 10.0
    elif preset == "Turnaround":
        st.session_state["opm_min"] = 10.0
        st.session_state["fcf_min"] = 0.0


st.sidebar.header("Presets")
col_p1, col_p2, col_p3 = st.sidebar.columns(3)
col_p1.button("Quality", on_click=apply_preset, args=("Quality",))
col_p2.button("Value", on_click=apply_preset, args=("Value",))
col_p3.button("Growth", on_click=apply_preset, args=("Growth",))

col_p4, col_p5, col_p6 = st.sidebar.columns(3)
col_p4.button("Dividend", on_click=apply_preset, args=("Dividend",))
col_p5.button("Debt-Free", on_click=apply_preset, args=("Debt-Free",))
col_p6.button("Turnaround", on_click=apply_preset, args=("Turnaround",))

st.sidebar.markdown("---")
st.sidebar.header("Custom Filters")

roe = st.sidebar.slider("ROE Min (%)", min_value=-50.0, max_value=100.0, key="roe_min")
de = st.sidebar.slider("D/E Max", min_value=0.0, max_value=10.0, key="de_max")
fcf = st.sidebar.slider(
    "FCF Min (Cr)", min_value=-10000.0, max_value=50000.0, key="fcf_min"
)
rev_cagr = st.sidebar.slider(
    "Rev CAGR 5y Min (%)", min_value=-50.0, max_value=100.0, key="rev_cagr_min"
)
pat_cagr = st.sidebar.slider(
    "PAT CAGR 5y Min (%)", min_value=-50.0, max_value=150.0, key="pat_cagr_min"
)
opm = st.sidebar.slider("OPM Min (%)", min_value=-50.0, max_value=100.0, key="opm_min")
pe = st.sidebar.slider("P/E Max", min_value=0.0, max_value=200.0, key="pe_max")
pb = st.sidebar.slider("P/B Max", min_value=0.0, max_value=50.0, key="pb_max")
div_yield = st.sidebar.slider(
    "Div Yield Min (%)", min_value=0.0, max_value=10.0, key="div_yield_min"
)
icr = st.sidebar.slider("ICR Min", min_value=-10.0, max_value=100.0, key="icr_min")

# Filter DataFrame
filtered_df = df.copy()

# Ensure columns are numeric for filtering
numeric_cols = [
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "revenue_cagr",
    "pat_cagr",
    "operating_profit_margin_pct",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
]

for c in numeric_cols:
    if c in filtered_df.columns:
        filtered_df[c] = pd.to_numeric(
            filtered_df[c].replace("Debt Free", 99999), errors="coerce"
        )

# Apply filters safely (if column exists)
if "return_on_equity_pct" in filtered_df:
    filtered_df = filtered_df[filtered_df["return_on_equity_pct"] >= roe]
if "debt_to_equity" in filtered_df:
    filtered_df = filtered_df[filtered_df["debt_to_equity"] <= de]
if "free_cash_flow_cr" in filtered_df:
    filtered_df = filtered_df[filtered_df["free_cash_flow_cr"] >= fcf]
if "revenue_cagr" in filtered_df:
    filtered_df = filtered_df[filtered_df["revenue_cagr"] >= rev_cagr]
if "pat_cagr" in filtered_df:
    filtered_df = filtered_df[filtered_df["pat_cagr"] >= pat_cagr]
if "operating_profit_margin_pct" in filtered_df:
    filtered_df = filtered_df[filtered_df["operating_profit_margin_pct"] >= opm]
if "pe_ratio" in filtered_df:
    filtered_df = filtered_df[filtered_df["pe_ratio"] <= pe]
if "pb_ratio" in filtered_df:
    filtered_df = filtered_df[filtered_df["pb_ratio"] <= pb]
if "dividend_yield_pct" in filtered_df:
    filtered_df = filtered_df[filtered_df["dividend_yield_pct"] >= div_yield]
if "interest_coverage" in filtered_df:
    filtered_df = filtered_df[filtered_df["interest_coverage"] >= icr]

# Format output table
display_cols = [
    "company_id",
    "company_name_company",
    "sector_name",
    "composite_score",
] + numeric_cols
display_df = filtered_df[[c for c in display_cols if c in filtered_df.columns]].copy()

# Rename columns for presentation
rename_map = {
    "company_id": "Ticker",
    "company_name_company": "Company Name",
    "sector_name": "Sector",
    "composite_score": "Quality Score",
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "D/E",
    "free_cash_flow_cr": "FCF (Cr)",
    "revenue_cagr": "Rev CAGR (%)",
    "pat_cagr": "PAT CAGR (%)",
    "operating_profit_margin_pct": "OPM (%)",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "dividend_yield_pct": "Div Yield (%)",
    "interest_coverage": "ICR",
}
display_df.rename(columns=rename_map, inplace=True)

# Round numeric columns
display_df = display_df.round(2)

st.markdown(f"### 🎯 {len(display_df)} companies match your filters")
st.dataframe(display_df, hide_index=True, use_container_width=True)

csv = display_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Export to CSV",
    data=csv,
    file_name="screener_results.csv",
    mime="text/csv",
)
