from fastapi import APIRouter, HTTPException
import math
import pandas as pd
from src.dashboard.utils.db import get_connection

router = APIRouter()

def clean_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

def df_to_dict(df):
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict('records')]

@router.get("/{ticker}")
def get_valuation(ticker: str):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM market_cap WHERE company_id = '{ticker}'", conn)
    conn.close()
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Valuation data not found")
        
    return df_to_dict(df)
