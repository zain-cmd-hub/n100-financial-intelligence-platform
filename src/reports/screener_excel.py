import logging
from pathlib import Path
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import sys
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from src.screener.engine import ScreenerEngine, PRESETS

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / "screener_output.xlsx"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_screener_excel():
    logger.info("Generating screener_output.xlsx...")
    writer = pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter")
    workbook = writer.book
    
    # Formats
    format_header = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white'})
    
    with ScreenerEngine() as engine:
        for preset_name, preset_config in PRESETS.items():
            df = engine.run_preset(preset_name)
            if df is not None and not df.empty:
                cols_to_keep = ["company_id", "company_name", "composite_score"]
                
                for k in preset_config.keys():
                    metric_name = k.replace("_min", "").replace("_max", "")
                    if metric_name not in cols_to_keep:
                        cols_to_keep.append(metric_name)
                
                important = ["return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "pe_ratio", "pb_ratio", "dividend_yield_pct", "net_profit_margin_pct", "pat_cagr", "revenue_cagr", "asset_turnover"]
                for i in important:
                    if i not in cols_to_keep and len(cols_to_keep) < 20:
                        cols_to_keep.append(i)
                
                final_cols = [c for c in cols_to_keep if c in df.columns]
                
                sheet_df = df[final_cols].copy()
                
                sheet_name = preset_name[:31]
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                
                for col_num, value in enumerate(sheet_df.columns.values):
                    worksheet.write(0, col_num, value, format_header)
                    worksheet.set_column(col_num, col_num, 15)
                    
    writer.close()
    logger.info(f"Successfully generated {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_screener_excel()
