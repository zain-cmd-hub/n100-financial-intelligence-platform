import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.screener.engine import ScreenerEngine
from src.screener.scoring import CompositeScorer

# Connect to database securely
DB_PATH = Path(__file__).resolve().parents[3] / "db" / "nifty100.db"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=600)
def get_companies():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM companies", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    conn = get_connection()
    query = f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}'"
    if year:
        query += f" AND year = '{year}'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM profitandloss WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_ratios(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_full_trends_data(ticker):
    pl = get_pl(ticker)
    ratios = get_ratios(ticker)
    
    if pl.empty and ratios.empty:
        return pd.DataFrame()
        
    if not pl.empty:
        pl['year'] = pl['year'].astype(str)
    if not ratios.empty:
        ratios['year'] = ratios['year'].astype(str)
        
    if not pl.empty and not ratios.empty:
        merged = pl.merge(ratios, on=['company_id', 'year'], how='outer')
    elif not pl.empty:
        merged = pl
    else:
        merged = ratios
        
    # Standardize columns we care about
    metrics = {
        'sales': 'Revenue',
        'net_profit': 'Net Profit',
        'eps': 'EPS',
        'free_cash_flow_cr': 'Free Cash Flow',
        'operating_profit': 'Operating Profit',
        'return_on_equity_pct': 'ROE (%)'
    }
    
    for c in metrics.keys():
        if c not in merged.columns:
            merged[c] = None
        else:
            # Handle "Debt Free" or weird strings
            merged[c] = pd.to_numeric(merged[c].replace("Debt Free", 0), errors='coerce')
            
    merged = merged.rename(columns=metrics)
    merged = merged.sort_values('year')
    return merged[['year'] + list(metrics.values())]

@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM balancesheet WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM cashflow WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_sectors():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM sectors", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_all_ratios():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM financial_ratios", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_prosandcons(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM prosandcons WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM peer_groups WHERE peer_group_name = '{group_name}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_peer_group_names():
    conn = get_connection()
    df = pd.read_sql("SELECT DISTINCT peer_group_name FROM peer_groups", conn)
    conn.close()
    return df['peer_group_name'].tolist()

@st.cache_data(ttl=600)
def get_valuation(ticker=None):
    try:
        val_path = Path(__file__).resolve().parents[3] / 'output' / 'valuation_summary.xlsx'
        df = pd.read_excel(val_path)
        if ticker:
            return df[df['company_id'] == ticker]
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_composite_scores():
    try:
        with ScreenerEngine() as engine:
            df = engine.merge_data()
            if df.empty:
                return pd.DataFrame()
            scorer = CompositeScorer(df)
            scored_df = scorer.calculate_score()
            # return only latest year
            scored_df = scored_df.sort_values(["company_id", "year"]).drop_duplicates(subset=["company_id"], keep="last")
            return scored_df[["company_id", "company_name_company", "sector_name", "composite_score"]].sort_values("composite_score", ascending=False)
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_screener_data():
    try:
        with ScreenerEngine() as engine:
            df = engine.merge_data()
            if df.empty:
                return pd.DataFrame()
            scorer = CompositeScorer(df)
            scored_df = scorer.calculate_score()
            # return only latest year for the screener
            scored_df = scored_df.sort_values(["company_id", "year"]).drop_duplicates(subset=["company_id"], keep="last")
            return scored_df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_documents(ticker):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM documents WHERE company_id = '{ticker}'", conn)
    conn.close()
    return df

