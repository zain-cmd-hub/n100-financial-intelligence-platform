import math

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.dashboard.utils.db import get_connection

router = APIRouter()


def clean_nan(val):
    """Handles operations for clean_nan."""
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def df_to_dict(df):
    """Handles operations for df_to_dict."""
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict("records")]


@router.get("/{ticker}")
def get_valuation(ticker: str):
    """Handles operations for get_valuation."""
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM market_cap WHERE company_id = '{ticker}'", conn)
    conn.close()

    if df.empty:
        raise HTTPException(status_code=404, detail="Valuation data not found")

    return df_to_dict(df)
