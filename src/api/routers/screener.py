from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import math
from src.dashboard.utils.db import get_screener_data

router = APIRouter()

def clean_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

def df_to_dict(df):
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict('records')]

@router.get("")
def screener(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    df = get_screener_data()
    if df.empty:
        return []
        
    try:
        if min_roe is not None:
            df = df[df['return_on_equity_pct'] >= min_roe]
        if max_de is not None:
            df = df[df['debt_to_equity'] <= max_de]
        if min_fcf is not None:
            df = df[df['free_cash_flow_cr'] >= min_fcf]
        if sector is not None:
            df = df[df['broad_sector'].str.lower() == sector.lower()]
        if min_rev_cagr_5yr is not None:
            df = df[df['revenue_cagr'] >= min_rev_cagr_5yr]
        if min_pat_cagr_5yr is not None:
            df = df[df['pat_cagr'] >= min_pat_cagr_5yr]
        if max_pe is not None:
            df = df[df['pe_ratio'] <= max_pe]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter values: {str(e)}")
        
    # ranked company list based on composite score (which get_screener_data already sorts by default)
    # just in case we can sort by composite score
    if 'composite_score' in df.columns:
        df = df.sort_values('composite_score', ascending=False)
        
    return df_to_dict(df)
