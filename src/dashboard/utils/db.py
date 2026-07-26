import sqlite3
import pandas as pd
import streamlit as st
from pathlib import Path

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
def get_peers(group_name):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM peer_groups WHERE peer_group_name = '{group_name}'", conn)
    conn.close()
    return df

@st.cache_data(ttl=600)
def get_valuation(ticker):
    # SAFE STUB for Day 22. Actual logic will be implemented in Day 26.
    return pd.DataFrame()
