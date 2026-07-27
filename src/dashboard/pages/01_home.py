import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_all_ratios, get_companies, get_sectors, get_composite_scores

st.title("Home")

# Sidebar - Year Selector
st.sidebar.header("Filters")
selected_year = st.sidebar.selectbox("Select Year", options=[2024, 2023, 2022, 2021, 2020, 2019])

# Load Data
ratios = get_all_ratios()
companies = get_companies()

# Filter by Year
ratios_yr = pd.DataFrame()
if not ratios.empty:
    ratios_yr = ratios[ratios['year'] == str(selected_year)].copy()
    if ratios_yr.empty:
        ratios_yr = ratios[ratios['year'] == selected_year].copy()

# KPIs Calculation
if not ratios_yr.empty:
    avg_roe = ratios_yr['return_on_equity_pct'].mean()
    median_pe = ratios_yr['pe_ratio'].median()
    
    # Handle D/E text values safely
    de_series = ratios_yr['debt_to_equity'].replace("Debt Free", 0)
    de_series = pd.to_numeric(de_series, errors='coerce')
    median_de = de_series.median()
    debt_free_count = (de_series == 0).sum()
    
    total_companies = ratios_yr['company_id'].nunique()
    
    median_rev_cagr = ratios_yr['revenue_cagr'].median() if 'revenue_cagr' in ratios_yr.columns else None
else:
    avg_roe = median_pe = median_de = total_companies = median_rev_cagr = debt_free_count = None

# 6 KPI Tiles
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Average ROE", f"{avg_roe:.2f}%" if pd.notna(avg_roe) else "N/A")
col2.metric("Median P/E", f"{median_pe:.2f}" if pd.notna(median_pe) else "N/A")
col3.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
col4.metric("Total Companies", f"{total_companies}" if pd.notna(total_companies) else "0")
col5.metric("Median Rev CAGR (5y)", f"{median_rev_cagr:.2f}%" if pd.notna(median_rev_cagr) else "N/A")
col6.metric("Debt-Free Companies", f"{debt_free_count}" if pd.notna(debt_free_count) else "0")

st.markdown("---")

col_chart, col_table = st.columns([1, 1])

with col_chart:
    st.subheader("Sector Breakdown")
    sectors_df = get_sectors()
    if not sectors_df.empty:
        # Group by broad_sector
        sector_counts = sectors_df['broad_sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        
        fig = px.pie(sector_counts, names='Sector', values='Count', hole=0.4, title="Companies by Sector")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No sector data available.")

with col_table:
    st.subheader("Top 5 Companies by Quality Score")
    scores_df = get_composite_scores()
    if not scores_df.empty:
        top_5 = scores_df.head(5).copy()
        top_5['composite_score'] = top_5['composite_score'].round(2)
        top_5.columns = ['Ticker', 'Company Name', 'Sector', 'Quality Score']
        st.dataframe(top_5, hide_index=True, use_container_width=True)
    else:
        st.info("Quality score data not available.")
