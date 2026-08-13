import math
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()


def clean_nan(val):
    """Handles operations for clean_nan."""
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def df_to_dict(df):
    """Handles operations for df_to_dict."""
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict("records")]


@router.get("/stats")
def get_portfolio_stats():
    """Handles operations for get_portfolio_stats."""
    stats_path = Path(__file__).resolve().parents[4] / "output" / "portfolio_stats.csv"
    if not stats_path.exists():
        raise HTTPException(status_code=404, detail="Portfolio stats not generated yet")

    df = pd.read_csv(stats_path)
    return df_to_dict(df)
