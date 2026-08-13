import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import (
    get_bs,
    get_companies,
    get_pl,
    get_prosandcons,
    get_ratios,
    get_sectors,
)

st.title("Company Profile")

# Load global data for search box
companies = get_companies()
sectors = get_sectors()

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
    st.info("Please select a company to view its profile.")
    st.stop()

ticker = selected_key.split(" - ")[0]
company_data = companies[companies["id"] == ticker].iloc[0]
sector_data = sectors[sectors["company_id"] == ticker]

# 1. Company Card
st.markdown("---")
col_card1, col_card2 = st.columns([1, 4])
with col_card1:
    if company_data["company_logo"]:
        st.image(company_data["company_logo"], width=100)
with col_card2:
    st.header(company_data["company_name"])
    st.caption(
        f"**Ticker:** {ticker} | **Sector:** {sector_data['broad_sector'].iloc[0] if not sector_data.empty else 'N/A'} | **Sub-Sector:** {sector_data['sub_sector'].iloc[0] if not sector_data.empty else 'N/A'}"
    )

st.markdown(f"**About:** {company_data['about_company']}")
st.markdown("---")

# Load company specific data
pl = get_pl(ticker)
ratios = get_ratios(ticker)
bs = get_bs(ticker)
pros_cons = get_prosandcons(ticker)

# Clean up years to strings to merge properly
if not pl.empty:
    pl["year"] = pl["year"].astype(str)
if not ratios.empty:
    ratios["year"] = ratios["year"].astype(str)
if not bs.empty:
    bs["year"] = bs["year"].astype(str)

latest_year = ratios["year"].max() if not ratios.empty else None
latest_ratios = (
    ratios[ratios["year"] == latest_year].iloc[0]
    if latest_year and not ratios.empty
    else None
)

# Calculate Revenue CAGR 5yr
rev_cagr = None
if not pl.empty and len(pl) >= 5:
    pl_sorted = pl.sort_values("year", ascending=True)
    sales_latest = pl_sorted.iloc[-1]["sales"]
    sales_5yr = pl_sorted.iloc[-5]["sales"]
    if pd.notna(sales_latest) and pd.notna(sales_5yr) and sales_5yr > 0:
        rev_cagr = ((sales_latest / sales_5yr) ** (1 / 5) - 1) * 100

# 2. 6 KPI Tiles
st.subheader(f"Key Performance Indicators ({latest_year})")
col1, col2, col3, col4, col5, col6 = st.columns(6)

roe = latest_ratios["return_on_equity_pct"] if latest_ratios is not None else None
roce = company_data["roce_percentage"]  # From companies table
npm = latest_ratios["net_profit_margin_pct"] if latest_ratios is not None else None
de = latest_ratios["debt_to_equity"] if latest_ratios is not None else None
fcf = latest_ratios["free_cash_flow_cr"] if latest_ratios is not None else None

col1.metric("ROE", f"{roe:.2f}%" if pd.notna(roe) else "N/A")
col2.metric("ROCE", f"{roce}%" if pd.notna(roce) else "N/A")
col3.metric("Net Profit Margin", f"{npm:.2f}%" if pd.notna(npm) else "N/A")
col4.metric("D/E Ratio", f"{de}" if pd.notna(de) else "N/A")
col5.metric("Rev CAGR 5yr", f"{rev_cagr:.2f}%" if rev_cagr is not None else "N/A")
col6.metric("Free Cash Flow", f"₹{fcf} Cr" if pd.notna(fcf) else "N/A")

st.markdown("---")

# 3. Charts
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("10-Year Revenue vs Net Profit")
    if not pl.empty:
        pl_chart = pl.tail(10).copy()
        pl_melted = pl_chart.melt(
            id_vars=["year"],
            value_vars=["sales", "net_profit"],
            var_name="Metric",
            value_name="Cr",
        )
        pl_melted["Metric"] = pl_melted["Metric"].map(
            {"sales": "Revenue", "net_profit": "Net Profit"}
        )
        fig1 = px.bar(
            pl_melted,
            x="year",
            y="Cr",
            color="Metric",
            barmode="group",
            title="Revenue & Net Profit (Cr)",
        )
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No P&L data available.")

with col_chart2:
    st.subheader("ROE vs ROCE (10 Years)")
    if not ratios.empty and not pl.empty and not bs.empty:
        merged = ratios[["year", "return_on_equity_pct"]].merge(
            pl[["year", "operating_profit"]], on="year"
        )
        merged = merged.merge(
            bs[["year", "equity_capital", "reserves", "borrowings"]], on="year"
        )

        # Calculate ROCE historical
        merged["capital_employed"] = (
            merged["equity_capital"] + merged["reserves"] + merged["borrowings"]
        )
        merged["ROCE"] = (merged["operating_profit"] / merged["capital_employed"]) * 100
        merged.rename(columns={"return_on_equity_pct": "ROE"}, inplace=True)

        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=merged["year"],
                y=merged["ROE"],
                name="ROE",
                mode="lines+markers",
                line={"color": "blue"},
            )
        )
        fig2.add_trace(
            go.Scatter(
                x=merged["year"],
                y=merged["ROCE"],
                name="ROCE",
                mode="lines+markers",
                line={"color": "orange"},
                yaxis="y2",
            )
        )

        fig2.update_layout(
            title="ROE & ROCE over Time",
            yaxis={
                "title": "ROE (%)",
                "titlefont": {"color": "blue"},
                "tickfont": {"color": "blue"},
            },
            yaxis2={
                "title": "ROCE (%)",
                "titlefont": {"color": "orange"},
                "tickfont": {"color": "orange"},
                "anchor": "x",
                "overlaying": "y",
                "side": "right",
            },
            hovermode="x unified",
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Historical ROE/ROCE data not available.")

st.markdown("---")

# 4. Pros & Cons
st.subheader("Pros & Cons")
if not pros_cons.empty:
    pros = pros_cons.iloc[0]["pro"]
    cons = pros_cons.iloc[0]["con"]

    col_p, col_c = st.columns(2)
    with col_p:
        st.markdown("### 🟢 Pros")
        for p in pros.split("|"):
            if p.strip():
                st.markdown(f"- {p.strip()}")
    with col_c:
        st.markdown("### 🔴 Cons")
        for c in cons.split("|"):
            if c.strip():
                st.markdown(f"- {c.strip()}")
else:
    st.info("No Pros & Cons data available for this company.")
