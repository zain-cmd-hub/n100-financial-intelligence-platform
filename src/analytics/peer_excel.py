import logging
from pathlib import Path
import warnings

import pandas as pd
import numpy as np

warnings.simplefilter(action='ignore', category=FutureWarning)

import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

try:
    from src.screener.engine import ScreenerEngine
    from src.screener.scoring import CompositeScorer
except ImportError:
    from engine import ScreenerEngine
    from scoring import CompositeScorer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PEER_GROUPS_FILE = BASE_DIR / "data" / "raw" / "peer_groups.xlsx"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "peer_comparison.xlsx"

METRICS = {
    "return_on_equity_pct": {"name": "ROE (%)", "inv": False},
    "roce_percentage": {"name": "ROCE (%)", "inv": False},
    "net_profit_margin_pct": {"name": "NPM (%)", "inv": False},
    "ebitda_margin_pct": {"name": "EBITDA Margin (%)", "inv": False},
    "debt_to_equity": {"name": "D/E", "inv": True},
    "interest_coverage": {"name": "Interest Coverage", "inv": False},
    "current_ratio": {"name": "Current Ratio", "inv": False},
    "asset_turnover": {"name": "Asset Turnover", "inv": False},
    "free_cash_flow_cr": {"name": "Free Cash Flow (Cr)", "inv": False},
    "sales": {"name": "Sales (Cr)", "inv": False},
    "net_profit": {"name": "Net Profit (Cr)", "inv": False},
    "earnings_per_share": {"name": "EPS", "inv": False},
    "pat_cagr": {"name": "PAT CAGR 5yr", "inv": False},
    "revenue_cagr": {"name": "Revenue CAGR 5yr", "inv": False},
    "eps_cagr": {"name": "EPS CAGR 5yr", "inv": False},
    "dividend_yield_pct": {"name": "Dividend Yield (%)", "inv": False},
    "pe_ratio": {"name": "P/E", "inv": True},
    "pb_ratio": {"name": "P/B", "inv": True},
    "debt_to_assets": {"name": "Debt to Assets", "inv": True},
    "composite_score": {"name": "Composite Score", "inv": False}
}

def generate_report():
    logger.info("Starting Peer Comparison Excel Report Generation...")
    
    with ScreenerEngine() as engine:
        df = engine.merge_data()
        df = df.dropna(subset=["company_id"]).copy()
        scorer = CompositeScorer(df)
        df = scorer.calculate_score()
        
    for col in METRICS.keys():
        if col not in df.columns:
            logger.warning(f"Missing column {col}, filling with NaN")
            df[col] = np.nan
        else:
            if df[col].dtype == object:
                if col == "debt_to_equity" or col == "debt_to_assets":
                    df[col] = df[col].replace({"Debt Free": 0})
                elif col == "interest_coverage":
                    df[col] = df[col].replace({"Debt Free": 999999})
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    try:
        peers_df = pd.read_excel(PEER_GROUPS_FILE)
    except Exception as e:
        logger.error(f"Failed to read peer groups: {e}")
        return
        
    df = df.merge(peers_df[["company_id", "peer_group_name", "is_benchmark"]].drop_duplicates(), on="company_id", how="left")
    df = df.dropna(subset=["peer_group_name"])
    
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    # Take latest year
    df = df.sort_values("year").groupby("company_id").last().reset_index()

    writer = pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter")
    workbook = writer.book
    
    # Formats
    format_pct_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100', 'num_format': '0.00'})
    format_pct_yellow = workbook.add_format({'bg_color': '#FFEB9C', 'font_color': '#9C5700', 'num_format': '0.00'})
    format_pct_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006', 'num_format': '0.00'})
    format_benchmark = workbook.add_format({'bg_color': '#FFC000', 'bold': True})
    format_num = workbook.add_format({'num_format': '0.00'})
    format_median = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'num_format': '0.00'})
    format_header = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white'})
    
    groups = df["peer_group_name"].unique()
    
    for group in groups:
        group_df = df[df["peer_group_name"] == group].copy()
        
        # Calculate ranks
        for col, info in METRICS.items():
            rank = group_df[col].rank(pct=True, ascending=True, na_option='bottom')
            if info["inv"]:
                rank = 1.0 - rank
            # Scale to 0-100 for better display
            group_df[f"{col}_pct"] = rank * 100
            
        # Reorder columns
        output_cols = ["company_id", "company_name", "is_benchmark"]
        for col in METRICS.keys():
            output_cols.append(col)
            output_cols.append(f"{col}_pct")
            
        group_df = group_df[output_cols]
        
        # Add Median row
        median_row = {"company_id": "MEDIAN", "company_name": "Peer Group Median", "is_benchmark": False}
        for col in METRICS.keys():
            median_row[col] = group_df[col].median()
            median_row[f"{col}_pct"] = np.nan
        group_df = pd.concat([group_df, pd.DataFrame([median_row])], ignore_index=True)
        
        # Clean up column names for Excel
        renamed = {"company_id": "Company ID", "company_name": "Company Name", "is_benchmark": "Benchmark"}
        for col, info in METRICS.items():
            renamed[col] = info["name"]
            renamed[f"{col}_pct"] = f"{info['name']} (Percentile)"
        
        group_df = group_df.rename(columns=renamed)
        
        # Keep sheet name <= 31 chars
        sheet_name = str(group).replace("/", "_").replace("\\", "_")[:31]
        group_df.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        
        # Write headers
        for col_num, value in enumerate(group_df.columns.values):
            worksheet.write(0, col_num, value, format_header)
            worksheet.set_column(col_num, col_num, 15)
            
        worksheet.set_column(0, 1, 20)
        
        # Apply formatting
        for row_num in range(1, len(group_df) + 1):
            is_median = (row_num == len(group_df))
            is_bench = group_df.iloc[row_num - 1].get("Benchmark", False)
            
            for col_num, col_name in enumerate(group_df.columns):
                val = group_df.iloc[row_num - 1, col_num]
                if pd.isna(val):
                    val = ""
                    
                cell_format = format_num
                if is_median:
                    cell_format = format_median
                elif is_bench:
                    cell_format = format_benchmark
                    
                if "(Percentile)" in col_name and val != "" and not is_median:
                    if float(val) >= 75:
                        cell_format = format_pct_green
                    elif float(val) <= 25:
                        cell_format = format_pct_red
                    else:
                        cell_format = format_pct_yellow
                        
                worksheet.write(row_num, col_num, val, cell_format)

    writer.close()
    logger.info(f"Successfully generated peer comparison report at {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_report()
