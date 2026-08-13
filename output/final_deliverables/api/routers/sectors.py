import math

from fastapi import APIRouter, HTTPException

from src.dashboard.utils.db import get_screener_data

router = APIRouter()


def clean_nan(val):
    """Handles operations for clean_nan."""
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def df_to_dict(df):
    """Handles operations for df_to_dict."""
    return [{k: clean_nan(v) for k, v in row.items()} for row in df.to_dict("records")]


@router.get("")
def list_sectors():
    """Handles operations for list_sectors."""
    # Return all 11 sectors with company_count, median_roe, median_pe, median_de
    df = get_screener_data()
    if df.empty:
        return []

    stats = []
    for sector, group in df.groupby("broad_sector"):
        stats.append(
            {
                "sector": sector,
                "company_count": len(group),
                "median_roe": clean_nan(group["return_on_equity_pct"].median()),
                "median_pe": clean_nan(group["pe_ratio"].median()),
                "median_de": clean_nan(group["debt_to_equity"].median()),
            }
        )
    return stats


@router.get("/{sector}/companies")
def get_companies_in_sector(sector: str):
    """Handles operations for get_companies_in_sector."""
    df = get_screener_data()
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not available")

    sector_df = df[df["broad_sector"].str.lower() == sector.lower()]
    if sector_df.empty:
        raise HTTPException(status_code=404, detail="Unknown sector")

    return df_to_dict(sector_df)
