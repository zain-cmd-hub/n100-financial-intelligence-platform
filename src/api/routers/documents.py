from fastapi import APIRouter, HTTPException
import math
import pandas as pd
from src.dashboard.utils.db import get_documents

router = APIRouter()

def clean_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

def df_to_dict(df):
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict('records')]

@router.get("/{ticker}/documents")
def get_company_documents(ticker: str):
    df = get_documents(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Documents not found")
        
    return df_to_dict(df)
