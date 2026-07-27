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
def get_valuation(ticker):
    # SAFE STUB for Day 22. Actual logic will be implemented in Day 26.
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
