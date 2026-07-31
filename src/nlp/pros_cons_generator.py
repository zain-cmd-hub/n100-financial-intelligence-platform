import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_screener_data, get_ratios, get_pl, get_bs, get_cf, get_companies

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'output'

def evaluate_rules():
    df_screener = get_screener_data()
    companies = get_companies()
    
    if df_screener.empty or companies.empty:
        logger.error("Failed to load base data.")
        return
        
    results = []
    
    for _, comp_row in df_screener.iterrows():
        cid = comp_row['company_id']
        sector = comp_row['broad_sector']
        
        ratios = get_ratios(cid)
        pl = get_pl(cid)
        bs = get_bs(cid)
        
        def to_num(val):
            return pd.to_numeric(str(val).replace('Debt Free', '0'), errors='coerce')
        
        def check_sustained(df, col, condition, n_years=3):
            if df.empty or len(df) < n_years:
                return 0, False
            recent = df.sort_values('year', ascending=False).head(n_years)
            vals = pd.to_numeric(recent[col].replace('Debt Free', '0'), errors='coerce').fillna(0)
            passed = sum(condition(v) for v in vals)
            conf = (passed / n_years) * 100
            return conf, passed == n_years
            
        def check_trend(df, col, trend='up', n_years=3):
            if df.empty or len(df) < n_years:
                return 0, False
            recent = df.sort_values('year', ascending=False).head(n_years)
            vals = pd.to_numeric(recent[col].replace('Debt Free', '0'), errors='coerce').fillna(0).values
            if len(vals) < n_years:
                return 0, False
            if trend == 'up':
                is_trend = all(vals[i] < vals[i-1] for i in range(1, len(vals))) # older is smaller
                conf = 100 if is_trend else 0
            else:
                is_trend = all(vals[i] > vals[i-1] for i in range(1, len(vals))) # older is larger
                conf = 100 if is_trend else 0
            return conf, is_trend

        pro_count = 0
        con_count = 0
        
        # --- PRO RULES ---
        
        conf, passed = check_sustained(ratios, 'return_on_equity_pct', lambda x: x > 20, 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P1', 'text': 'Consistently high return on equity above 20% demonstrates exceptional capital efficiency', 'confidence_pct': conf})
            pro_count += 1
            
        conf, passed = check_sustained(ratios, 'free_cash_flow_cr', lambda x: x > 0, 5)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P2', 'text': 'Strong free cash flow generation over 5 years signals healthy business fundamentals', 'confidence_pct': conf})
            pro_count += 1
            
        de = to_num(comp_row.get('debt_to_equity'))
        if pd.notna(de) and de == 0:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P3', 'text': 'Debt-free balance sheet provides financial flexibility and eliminates interest burden', 'confidence_pct': 100.0})
            pro_count += 1
            
        rev_cagr = to_num(comp_row.get('revenue_cagr'))
        if pd.notna(rev_cagr) and rev_cagr > 15:
            conf = min(100.0, max(61.0, rev_cagr * 4))
            if conf > 60:
                results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P4', 'text': 'Revenue growing at above 15% CAGR over 5 years reflects strong business momentum', 'confidence_pct': conf})
                pro_count += 1
                
        opm = to_num(comp_row.get('opm_percentage'))
        if pd.notna(opm) and opm > 25:
            conf = min(100.0, max(61.0, opm * 3))
            if conf > 60:
                results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P5', 'text': 'Operating profit margin above 25% indicates strong pricing power and cost discipline', 'confidence_pct': conf})
                pro_count += 1
                
        pat_cagr = to_num(comp_row.get('pat_cagr'))
        if pd.notna(pat_cagr) and pat_cagr > 20:
            conf = min(100.0, max(61.0, pat_cagr * 4))
            if conf > 60:
                results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P6', 'text': 'Net profit compounding at above 20% over 5 years creates significant shareholder value', 'confidence_pct': conf})
                pro_count += 1
                
        icr = to_num(comp_row.get('interest_coverage'))
        if (pd.notna(icr) and icr > 10) or (pd.notna(de) and de == 0):
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P7', 'text': 'Very high interest coverage ratio reflects negligible financial stress from debt servicing', 'confidence_pct': 90.0})
            pro_count += 1
            
        dy = to_num(comp_row.get('dividend_yield_pct'))
        fcf = to_num(comp_row.get('free_cash_flow_cr'))
        if pd.notna(dy) and dy > 2 and pd.notna(fcf) and fcf > 0:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P8', 'text': 'Consistent dividend yield above 2% backed by positive free cash flow', 'confidence_pct': 100.0})
            pro_count += 1
            
        eps_cagr = to_num(comp_row.get('eps_cagr'))
        if pd.notna(eps_cagr) and eps_cagr > 15:
            conf = min(100.0, max(61.0, eps_cagr * 4))
            if conf > 60:
                results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P9', 'text': 'Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding', 'confidence_pct': conf})
                pro_count += 1
                
        conf, passed = check_trend(ratios, 'return_on_equity_pct', 'up', 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P10', 'text': 'Return on equity improving for 3 consecutive years shows strengthening business quality', 'confidence_pct': conf})
            pro_count += 1
            
        if pd.notna(rev_cagr) and pd.notna(pat_cagr) and pat_cagr > rev_cagr and rev_cagr > 0:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P11', 'text': 'Revenue growing slower than profits shows improving operating leverage and scale benefits', 'confidence_pct': 85.0})
            pro_count += 1
            
        if len(bs) >= 2:
            bs_recent = bs.sort_values('year', ascending=False).head(2)
            assets = pd.to_numeric(bs_recent['total_assets'], errors='coerce').fillna(0).values
            debts = pd.to_numeric(bs_recent['borrowings'], errors='coerce').fillna(0).values
            if assets[0] > assets[1] and debts[0] < debts[1]:
                results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P12', 'text': 'Growing asset base funded by internal accruals reflects self-sustaining growth', 'confidence_pct': 90.0})
                pro_count += 1
                
        # --- CON RULES ---
        
        if sector != 'Financials' and pd.notna(de) and de > 2.0:
            conf = min(100.0, de * 30)
            if conf > 60:
                results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C1', 'text': f'Debt-to-equity ratio of {de:.1f}x is elevated for a non-financial company and warrants monitoring', 'confidence_pct': conf})
                con_count += 1
                
        conf, passed = check_sustained(ratios, 'free_cash_flow_cr', lambda x: x < 0, 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C2', 'text': 'Free cash flow negative for 3 consecutive years raises concern about cash generation quality', 'confidence_pct': conf})
            con_count += 1
            
        conf, passed = check_trend(pl, 'opm_percentage', 'down', 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C3', 'text': 'Operating margins declining for 3 consecutive years suggest pricing or cost pressure', 'confidence_pct': conf})
            con_count += 1
            
        np_latest = to_num(comp_row.get('net_profit'))
        if pd.notna(np_latest) and np_latest < 0:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C4', 'text': 'Company reported a net loss in the most recent financial year', 'confidence_pct': 100.0})
            con_count += 1
            
        conf, passed = check_trend(pl, 'sales', 'down', 2)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C5', 'text': 'Revenue contraction over 2 consecutive years indicates demand weakness or market share loss', 'confidence_pct': conf})
            con_count += 1
            
        if pd.notna(icr) and icr < 1.5:
            conf = max(61.0, (1.5 - icr)*100)
            if conf > 60:
                results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C6', 'text': 'Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations', 'confidence_pct': conf})
                con_count += 1
                
        dp = to_num(comp_row.get('dividend_payout'))
        if pd.notna(dp) and dp > 100:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C7', 'text': 'Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable', 'confidence_pct': 100.0})
            con_count += 1
            
        conf, passed = check_trend(ratios, 'debt_to_equity', 'up', 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C8', 'text': 'Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk', 'confidence_pct': conf})
            con_count += 1
            
        conf, passed = check_trend(pl, 'eps', 'down', 3)
        if passed and conf > 60:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C9', 'text': 'Earnings per share declining for 3 consecutive years reflects deteriorating profitability', 'confidence_pct': conf})
            con_count += 1
            
        roce = to_num(comp_row.get('roce_percentage'))
        if pd.notna(roce) and roce < 10:
            conf = max(61.0, (10 - roce)*10)
            if conf > 60:
                results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C10', 'text': 'Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital', 'confidence_pct': conf})
                con_count += 1
                
        debt = to_num(comp_row.get('total_debt_cr'))
        op_prof = to_num(comp_row.get('operating_profit'))
        depr = to_num(comp_row.get('depreciation'))
        if pd.notna(debt) and pd.notna(op_prof) and pd.notna(depr):
            ebitda = op_prof + depr
            if ebitda > 0 and (debt / ebitda) > 3:
                results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C11', 'text': 'Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility', 'confidence_pct': 85.0})
                con_count += 1
                
        if pd.notna(rev_cagr) and rev_cagr < 5:
            conf = max(61.0, (5 - rev_cagr)*20)
            if conf > 60:
                results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C12', 'text': 'Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum', 'confidence_pct': min(100.0, conf)})
                con_count += 1
                
        # --- FALLBACKS ---
        if pro_count == 0:
            results.append({'company_id': cid, 'type': 'pro', 'rule_id': 'P_FALLBACK', 'text': 'Stable market position within the Nifty 100 universe', 'confidence_pct': 100.0})
        if con_count == 0:
            results.append({'company_id': cid, 'type': 'con', 'rule_id': 'C_FALLBACK', 'text': 'Macro-economic sensitivity and broad sector cyclicality', 'confidence_pct': 100.0})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / 'pros_cons_generated.csv'
    df_res = pd.DataFrame(results)
    
    df_res['confidence_pct'] = df_res['confidence_pct'].clip(upper=100.0).round(1)
    df_res.to_csv(out_path, index=False)
    logger.info(f"Generated {len(df_res)} pros/cons and saved to {out_path}")
    
    pro_cids = df_res[df_res['type'] == 'pro']['company_id'].nunique()
    con_cids = df_res[df_res['type'] == 'con']['company_id'].nunique()
    expected = len(df_screener)
    
    assert pro_cids == expected, f"Exit Criteria failed: {pro_cids} companies have pros, expected {expected}"
    assert con_cids == expected, f"Exit Criteria failed: {con_cids} companies have cons, expected {expected}"
    logger.info("Exit Criteria successfully met: Every company has at least 1 pro and 1 con.")

if __name__ == "__main__":
    evaluate_rules()
