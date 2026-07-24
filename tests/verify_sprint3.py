import os
import sys
from pathlib import Path
import pandas as pd
import sqlite3
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.screener.engine import ScreenerEngine

def verify_screener():
    print("Verifying Screener Output...")
    output_file = Path("output/screener_output.xlsx")
    assert output_file.exists(), "screener_output.xlsx does not exist!"
    
    xls = pd.ExcelFile(output_file)
    assert len(xls.sheet_names) == 4, f"Expected 4 sheets, got {len(xls.sheet_names)}"
    
    if "quality" in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name="quality")
        # Quality Compounder preset: ROE > 15%, D/E < 1.0
        top_5 = df.head(5)
        for idx, row in top_5.iterrows():
            roe = row.get("return_on_equity_pct")
            de = row.get("debt_to_equity")
            if pd.notna(roe):
                assert roe >= 15.0, f"Company {row['company_name']} has ROE < 15: {roe}"
            if pd.notna(de):
                try:
                    de_val = float(de)
                    assert de_val <= 1.0, f"Company {row['company_name']} has D/E > 1.0: {de_val}"
                except ValueError:
                    pass  # Debt Free
    print("PASS: Screener Output verification.")

def verify_peer_rankings():
    print("Verifying Peer Rankings...")
    db_path = Path("db/nifty100.db")
    assert db_path.exists(), "Database not found."
    
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM peer_percentiles WHERE peer_group_name = 'IT Services' AND metric = 'ROE' AND year = 2024", conn)
    conn.close()
    
    if df.empty:
        print("SKIP: IT Services group not found in peer_percentiles.")
        return
        
    df["value"] = pd.to_numeric(df["value"])
    df["percentile_rank"] = pd.to_numeric(df["percentile_rank"])
    
    max_roe_idx = df["value"].idxmax()
    max_rank_idx = df["percentile_rank"].idxmax()
    
    assert max_roe_idx == max_rank_idx, "The company with the highest ROE does not have the highest percentile rank!"
    print("PASS: Peer Rankings verification.")

def verify_files():
    print("Verifying Deliverables...")
    assert Path("output/peer_comparison.xlsx").exists(), "peer_comparison.xlsx missing"
    assert len(list(Path("reports/radar_charts").glob("*.png"))) > 0, "Radar charts missing"
    print("PASS: File verification.")

if __name__ == "__main__":
    try:
        verify_screener()
        verify_peer_rankings()
        verify_files()
        print("\nALL SPRINT 3 VERIFICATIONS PASSED SUCCESSFULLY!")
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
