from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math
from src.dashboard.utils.db import (
    get_screener_data, get_pl, get_bs, get_cf, get_ratios, get_companies
)
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

def clean_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

def df_to_dict(df):
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict('records')]

@router.get("")
def list_companies(
    sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None
):
    df = get_screener_data()
    if df.empty:
        return []
        
    if sector:
        df = df[df['broad_sector'].str.lower() == sector.lower()]
    if market_cap_category:
        df = df[df['market_cap_category'].str.lower() == market_cap_category.lower()]
    if search:
        search_lower = search.lower()
        df = df[df['company_name'].str.lower().str.contains(search_lower) | 
                df['company_id'].str.lower().str.contains(search_lower)]
        
    res = df[['company_id', 'company_name', 'broad_sector', 'sub_sector', 'return_on_equity_pct', 'roce_percentage']].copy()
    res = res.rename(columns={'company_id': 'id', 'return_on_equity_pct': 'roe_pct', 'roce_percentage': 'roce_pct'})
    return df_to_dict(res)

@router.get("/{ticker}")
def get_company_profile(ticker: str):
    df = get_screener_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not available")
        
    company = df[df['company_id'] == ticker]
    if company.empty:
        raise HTTPException(status_code=404, detail="Company not found")
        
    return df_to_dict(company)[0]

def filter_by_year(df, from_year: str, to_year: str):
    if df.empty or 'year' not in df.columns:
        return df
    if from_year:
        df = df[df['year'] >= from_year]
    if to_year:
        df = df[df['year'] <= to_year]
    return df

@router.get("/{ticker}/pl")
def get_company_pl(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    df = get_pl(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Company or data not found")
    df = filter_by_year(df, from_year, to_year)
    return df_to_dict(df)

@router.get("/{ticker}/bs")
def get_company_bs(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    df = get_bs(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Company or data not found")
    df = filter_by_year(df, from_year, to_year)
    return df_to_dict(df)

@router.get("/{ticker}/cashflow")
def get_company_cf(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    df = get_cf(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Company or data not found")
    df = filter_by_year(df, from_year, to_year)
    return df_to_dict(df)

@router.get("/{ticker}/ratios")
def get_company_ratios(ticker: str, year: Optional[str] = None):
    df = get_ratios(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Company or data not found")
    if year:
        df = df[df['year'] == year]
        if df.empty:
            raise HTTPException(status_code=404, detail="Data for year not found")
        return df_to_dict(df)[0]
    return df_to_dict(df)

@router.get("/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    file_path = Path(__file__).resolve().parents[4] / "output" / "tearsheets" / f"{ticker}_tearsheet.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Tearsheet not found")
    return FileResponse(file_path, media_type='application/pdf', filename=f"{ticker}_tearsheet.pdf")

@router.get("/{ticker}/peers/compare")
def get_company_peers_compare(ticker: str):
    from src.dashboard.utils.db import get_connection
    import pandas as pd
    
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM peer_percentiles WHERE company_id = '{ticker}'", conn)
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Peer comparison data not found for company")
        
    return df_to_dict(df)
