from fastapi import APIRouter, HTTPException
import math
import pandas as pd
from pathlib import Path

router = APIRouter()

def clean_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return None
    return val

def df_to_dict(df):
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict('records')]

@router.get("/stats")
def get_portfolio_stats():
    stats_path = Path(__file__).resolve().parents[4] / "output" / "portfolio_stats.csv"
    if not stats_path.exists():
        raise HTTPException(status_code=404, detail="Portfolio stats not generated yet")
        
    df = pd.read_csv(stats_path)
    return df_to_dict(df)
