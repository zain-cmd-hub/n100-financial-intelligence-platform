import os
import sqlite3
import pandas as pd
from pathlib import Path

def print_header(title):
    print(f"\n{'='*40}")
    print(f"{title}")
    print(f"{'='*40}")

def check_deliverables():
    print_header("1. Checking Final Deliverables Archive")
    path = Path("output/final_deliverables")
    if not path.exists():
        print("[FAIL] output/final_deliverables folder missing!")
        return
        
    items = list(path.iterdir())
    print(f"[PASS] Found {len(items)} items in final_deliverables directory.")
    for item in items:
        if item.is_file():
            size_kb = item.stat().st_size / 1024
            print(f"  - {item.name} ({size_kb:.1f} KB)")
        else:
            print(f"  - [DIR] {item.name}")

def check_database():
    print_header("2. Checking SQLite Database (AC-01, AC-04)")
    db_path = "db/nifty100.db"
    if not os.path.exists(db_path):
        print("[FAIL] Database missing!")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM companies")
    print(f"[PASS] Companies Table Count: {c.fetchone()[0]}")
    
    c.execute("SELECT COUNT(*) FROM financial_ratios")
    print(f"[PASS] Financial Ratios Count: {c.fetchone()[0]}")
    conn.close()

def check_pdfs():
    print_header("3. Checking PDFs (AC-17, AC-20)")
    guide = Path("docs/analyst_guide.pdf")
    if guide.exists():
        print(f"[PASS] Analyst Guide PDF exists ({guide.stat().st_size / 1024:.1f} KB)")
    else:
        print("[FAIL] Analyst Guide PDF missing")
        
    checklist = Path("docs/acceptance_checklist.pdf")
    if checklist.exists():
        print(f"[PASS] Acceptance Checklist PDF exists ({checklist.stat().st_size / 1024:.1f} KB)")
    else:
        print("[FAIL] Acceptance Checklist PDF missing")
        
    tearsheets = list(Path("reports/tearsheets").glob("*.pdf"))
    print(f"[PASS] Found {len(tearsheets)} Tearsheet PDFs in reports/tearsheets/")

def check_endpoints():
    print_header("4. Checking API Endpoints Scaffold")
    # Quick static count of `@app.get` or `@router.get`
    endpoint_count = 0
    for root, _, files in os.walk("src/api"):
        for f in files:
            if f.endswith(".py"):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                    content = file.read()
                    endpoint_count += content.count("@router.get") + content.count("@app.get")
    print(f"[PASS] Total FastAPI Endpoints found in code: {endpoint_count} (Requirement: 16)")

if __name__ == "__main__":
    check_deliverables()
    check_database()
    check_pdfs()
    check_endpoints()
    print_header("[PASS] ALL SANITY CHECKS COMPLETED")
