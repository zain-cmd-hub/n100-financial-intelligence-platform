import sqlite3
import time
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

START_TIME = time.time()
DB_PATH = Path(__file__).resolve().parents[3] / "db" / "nifty100.db"


@router.get("/health")
def health_check():
    """Handles operations for health_check."""
    uptime = int(time.time() - START_TIME)
    tables = [
        "companies",
        "profit_loss",
        "balance_sheet",
        "cash_flow",
        "financial_ratios",
        "market_data",
        "shareholding",
        "price_history",
        "documents",
        "peer_percentiles",
    ]

    db_row_counts = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # We might not have all tables created perfectly based on earlier sprint definitions,
        # so we will gracefully handle missing tables.
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                db_row_counts[t] = cursor.fetchone()[0]
            except Exception:
                db_row_counts[t] = 0

        conn.close()
    except Exception:
        pass

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "db_row_counts": db_row_counts,
    }
