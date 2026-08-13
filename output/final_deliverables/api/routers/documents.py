import math

from fastapi import APIRouter, HTTPException

from src.dashboard.utils.db import get_documents

router = APIRouter()


def clean_nan(val):
    """Handles operations for clean_nan."""
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def df_to_dict(df):
    """Handles operations for df_to_dict."""
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict("records")]


@router.get("/{ticker}/documents")
def get_company_documents(ticker: str):
    """Handles operations for get_company_documents."""
    df = get_documents(ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Documents not found")

    return df_to_dict(df)
