import os
import io
import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys
import matplotlib.pyplot as plt

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_screener_data, get_pl, get_ratios, get_bs, get_cf

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'output' / 'tearsheets'

# Data Loaders for NLP and Cashflow Intel
PROS_CONS_PATH = Path(__file__).resolve().parents[2] / 'output' / 'pros_cons_generated.csv'
CF_INTEL_PATH = Path(__file__).resolve().parents[2] / 'output' / 'cashflow_intelligence.xlsx'

def get_company_name(ticker):
    df = get_screener_data()
    row = df[df['company_id'] == ticker]
    if not row.empty:
        return row.iloc[0].get('company_name_company', ticker)
    return ticker

def get_kpis(ticker):
    df = get_screener_data()
    row = df[df['company_id'] == ticker]
    if row.empty:
        return {}
    row = row.iloc[0]
    
    # Extract 6 KPIs
    try:
        cmp_val = f"₹ {row.get('cmp', 0):,.2f}"
    except:
        cmp_val = "N/A"
        
    try:
        mcap = f"₹ {row.get('market_cap', 0):,.0f} Cr"
    except:
        mcap = "N/A"
        
    try:
        pe = f"{row.get('pe', 0):.2f}"
    except:
        pe = "N/A"
        
    fcf_cagr = f"{row.get('free_cash_flow_cagr', 0):.2f}%"
    
    # Try to get CFO quality from CF_INTEL
    cfo_quality = "Unknown"
    if CF_INTEL_PATH.exists():
        cf_intel = pd.read_excel(CF_INTEL_PATH)
        intel_row = cf_intel[cf_intel['company_id'] == ticker]
        if not intel_row.empty:
            cfo_quality = str(intel_row.iloc[0].get('cfo_quality_label', 'Unknown'))
            
    comp_score = f"{row.get('composite_score', 0):.2f}"
    
    return {
        "CMP": cmp_val,
        "Market Cap": mcap,
        "P/E Ratio": pe,
        "FCF CAGR 5Yr": fcf_cagr,
        "CFO Quality": cfo_quality,
        "Comp. Score": comp_score
    }

def get_nlp_points(ticker):
    pros = []
    cons = []
    if PROS_CONS_PATH.exists():
        df = pd.read_csv(PROS_CONS_PATH)
        df_comp = df[df['company_id'] == ticker]
        for _, r in df_comp.iterrows():
            if r['type'].lower() == 'pro':
                pros.append(r['text'])
            elif r['type'].lower() == 'con':
                cons.append(r['text'])
    return pros, cons

def get_capital_allocation(ticker):
    if CF_INTEL_PATH.exists():
        cf_intel = pd.read_excel(CF_INTEL_PATH)
        intel_row = cf_intel[cf_intel['company_id'] == ticker]
        if not intel_row.empty:
            return str(intel_row.iloc[0].get('capital_allocation_label', 'Unknown'))
    return "Unknown"

# ---- Chart Generators (Returns io.BytesIO) ----
def chart_rev_pat(ticker):
    pl = get_pl(ticker)
    if pl.empty: return None
    pl = pl.sort_values('year').tail(10)
    
    fig, ax = plt.subplots(figsize=(6, 3))
    x = np.arange(len(pl['year']))
    width = 0.35
    
    rev = pd.to_numeric(pl['sales'], errors='coerce').fillna(0)
    pat = pd.to_numeric(pl['net_profit'], errors='coerce').fillna(0)
    
    ax.bar(x - width/2, rev, width, label='Revenue', color='#2b5c8f')
    ax.bar(x + width/2, pat, width, label='Net Profit', color='#5ab4ac')
    
    ax.set_xticks(x)
    ax.set_xticklabels(pl['year'], rotation=45, ha='right', fontsize=8)
    ax.set_title("10-Year Revenue & Net Profit (Cr)", fontsize=10)
    ax.legend(fontsize=8)
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

def chart_roe_roce(ticker):
    ratios = get_ratios(ticker)
    if ratios.empty: return None
    ratios = ratios.sort_values('year').tail(10)
    
    fig, ax1 = plt.subplots(figsize=(6, 3))
    x = np.arange(len(ratios['year']))
    
    if 'return_on_equity_pct' not in ratios.columns: ratios['return_on_equity_pct'] = 0
    if 'return_on_capital_employed_pct' not in ratios.columns: ratios['return_on_capital_employed_pct'] = 0
    
    roe = pd.to_numeric(ratios['return_on_equity_pct'], errors='coerce').fillna(0)
    roce = pd.to_numeric(ratios['return_on_capital_employed_pct'], errors='coerce').fillna(0)
    
    ax1.plot(x, roe, marker='o', color='#d95f02', label='ROE (%)')
    ax1.set_ylabel('ROE (%)', color='#d95f02', fontsize=8)
    ax1.tick_params(axis='y', labelcolor='#d95f02', labelsize=8)
    
    ax2 = ax1.twinx()
    ax2.plot(x, roce, marker='s', color='#7570b3', label='ROCE (%)')
    ax2.set_ylabel('ROCE (%)', color='#7570b3', fontsize=8)
    ax2.tick_params(axis='y', labelcolor='#7570b3', labelsize=8)
    
    ax1.set_xticks(x)
    ax1.set_xticklabels(ratios['year'], rotation=45, ha='right', fontsize=8)
    plt.title("10-Year ROE & ROCE", fontsize=10)
    
    fig.legend(loc="upper left", bbox_to_anchor=(0.1,0.9), bbox_transform=ax1.transAxes, fontsize=8)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

def chart_bs_composition(ticker):
    bs = get_bs(ticker)
    if bs.empty: return None
    bs = bs.sort_values('year').tail(10)
    
    fig, ax = plt.subplots(figsize=(6, 3))
    
    if 'equity_share_capital' not in bs.columns: bs['equity_share_capital'] = 0
    if 'reserves' not in bs.columns: bs['reserves'] = 0
    if 'borrowings' not in bs.columns: bs['borrowings'] = 0
    if 'other_liabilities' not in bs.columns: bs['other_liabilities'] = 0
    
    eq = pd.to_numeric(bs['equity_share_capital'], errors='coerce').fillna(0) + \
         pd.to_numeric(bs['reserves'], errors='coerce').fillna(0)
    borr = pd.to_numeric(bs['borrowings'], errors='coerce').fillna(0)
    other = pd.to_numeric(bs['other_liabilities'], errors='coerce').fillna(0)
    
    x = bs['year']
    
    ax.bar(x, eq, label='Equity', color='#1b9e77')
    ax.bar(x, borr, bottom=eq, label='Borrowings', color='#d95f02')
    ax.bar(x, other, bottom=eq+borr, label='Other Liab', color='#7570b3')
    
    plt.xticks(rotation=45, ha='right', fontsize=8)
    plt.yticks(fontsize=8)
    plt.title("Balance Sheet Composition", fontsize=10)
    plt.legend(fontsize=8)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

def chart_cf_waterfall(ticker):
    cf = get_cf(ticker)
    if cf.empty: return None
    latest = cf.sort_values('year').tail(1).iloc[0]
    
    cfo = pd.to_numeric(latest.get('operating_activity', 0), errors='coerce')
    cfi = pd.to_numeric(latest.get('investing_activity', 0), errors='coerce')
    cff = pd.to_numeric(latest.get('financing_activity', 0), errors='coerce')
    
    if pd.isna(cfo): cfo = 0
    if pd.isna(cfi): cfi = 0
    if pd.isna(cff): cff = 0
    
    net = cfo + cfi + cff
    
    labels = ['CFO', 'CFI', 'CFF', 'Net CF']
    values = [cfo, cfi, cff, net]
    
    fig, ax = plt.subplots(figsize=(6, 3))
    colors_list = ['#1b9e77' if v >= 0 else '#d95f02' for v in values]
    
    ax.bar(labels, values, color=colors_list)
    plt.title(f"Cash Flow Waterfall ({latest['year']})", fontsize=10)
    plt.axhline(0, color='black', linewidth=0.8)
    
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:,.0f}", ha='center', va='bottom' if v>=0 else 'top', fontsize=8)
        
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


def build_tearsheet(ticker):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUTPUT_DIR / f"{ticker}_Tearsheet.pdf"
    
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_header = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.white,
        backColor=colors.HexColor('#1f497d'),
        alignment=1,
        spaceAfter=20,
        spaceBefore=0,
        borderPadding=10
    )
    
    style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], spaceAfter=10, textColor=colors.HexColor('#1f497d'))
    
    # Word wrap styles for tables/lists
    style_normal = styles['Normal']
    style_pro = ParagraphStyle('Pro', parent=style_normal, spaceAfter=5, textColor=colors.black)
    style_con = ParagraphStyle('Con', parent=style_normal, spaceAfter=5, textColor=colors.black)
    
    story = []
    
    # --- PAGE 1 ---
    comp_name = get_company_name(ticker)
    story.append(Paragraph(f"<b>{comp_name} ({ticker})</b> - Financial Tearsheet", style_header))
    
    # KPIs (2 rows of 3)
    kpis = get_kpis(ticker)
    kpi_keys = list(kpis.keys())
    
    if len(kpi_keys) >= 6:
        row1 = [
            Paragraph(f"<b>{kpi_keys[0]}</b><br/>{kpis[kpi_keys[0]]}", style_normal),
            Paragraph(f"<b>{kpi_keys[1]}</b><br/>{kpis[kpi_keys[1]]}", style_normal),
            Paragraph(f"<b>{kpi_keys[2]}</b><br/>{kpis[kpi_keys[2]]}", style_normal)
        ]
        row2 = [
            Paragraph(f"<b>{kpi_keys[3]}</b><br/>{kpis[kpi_keys[3]]}", style_normal),
            Paragraph(f"<b>{kpi_keys[4]}</b><br/>{kpis[kpi_keys[4]]}", style_normal),
            Paragraph(f"<b>{kpi_keys[5]}</b><br/>{kpis[kpi_keys[5]]}", style_normal)
        ]
        
        kpi_table = Table([row1, row2], colWidths=[2*inch, 2*inch, 2*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f5fa')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('INNERGRID', (0,0), (-1,-1), 1, colors.white),
            ('BOX', (0,0), (-1,-1), 1, colors.white),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 20))
    
    story.append(Paragraph("<b>Performance Trends</b>", style_h2))
    
    # Charts (Side by Side in a Table)
    buf_rev = chart_rev_pat(ticker)
    buf_roe = chart_roe_roce(ticker)
    
    img_rev = Image(buf_rev, width=3.2*inch, height=1.6*inch) if buf_rev else Paragraph("No Data", style_normal)
    img_roe = Image(buf_roe, width=3.2*inch, height=1.6*inch) if buf_roe else Paragraph("No Data", style_normal)
    
    chart_table = Table([[img_rev, img_roe]])
    chart_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(chart_table)
    
    story.append(PageBreak())
    
    # --- PAGE 2 ---
    story.append(Paragraph("<b>Capital Structure & Cash Flow</b>", style_h2))
    
    buf_bs = chart_bs_composition(ticker)
    buf_cf = chart_cf_waterfall(ticker)
    
    img_bs = Image(buf_bs, width=3.2*inch, height=1.6*inch) if buf_bs else Paragraph("No Data", style_normal)
    img_cf = Image(buf_cf, width=3.2*inch, height=1.6*inch) if buf_cf else Paragraph("No Data", style_normal)
    
    chart_table2 = Table([[img_bs, img_cf]])
    chart_table2.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(chart_table2)
    story.append(Spacer(1, 20))
    
    # Capital Allocation Badge
    cap_alloc = get_capital_allocation(ticker)
    story.append(Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_alloc}", style_h2))
    story.append(Spacer(1, 10))
    
    # Pros & Cons
    pros, cons = get_nlp_points(ticker)
    
    story.append(Paragraph("<b>Key Strengths (Pros)</b>", style_h2))
    if pros:
        for p in pros:
            # Wordwrap natively supported by ReportLab Paragraphs
            story.append(Paragraph(f"<font color='green'>•</font> {p}", style_pro))
    else:
        story.append(Paragraph("No pros identified.", style_normal))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Key Risks & Weaknesses (Cons)</b>", style_h2))
    if cons:
        for c in cons:
            story.append(Paragraph(f"<font color='red'>•</font> {c}", style_con))
    else:
        story.append(Paragraph("No cons identified.", style_normal))

    # Build PDF
    try:
        doc.build(story)
        logger.info(f"Generated Tearsheet for {ticker}")
    except Exception as e:
        logger.error(f"Failed to build PDF for {ticker}: {e}")

def generate_all():
    df = get_screener_data()
    all_tickers = df['company_id'].unique()
    skipped = []
    
    logger.info(f"Starting batch generation for {len(all_tickers)} companies...")
    for t in all_tickers:
        pl = get_pl(t)
        if pl is None or pl.empty or len(pl['year'].unique()) < 3:
            logger.warning(f"Skipping {t} - Insufficient data (< 3 years)")
            skipped.append(t)
            continue
        build_tearsheet(t)
        
    # Log skipped
    skip_path = Path(__file__).resolve().parents[2] / 'output' / 'skipped_tearsheets.csv'
    pd.DataFrame({'company_id': skipped}).to_csv(skip_path, index=False)
    logger.info(f"Batch generation complete. Generated: {len(all_tickers) - len(skipped)}, Skipped: {len(skipped)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--batch':
        generate_all()
    else:
        test_tickers = ['TCS', 'HDFCBANK', 'RELIANCE', 'SUNPHARMA', 'TATASTEEL']
        logger.info("Starting Batch Test for Day 33 Tearsheets...")
        for t in test_tickers:
            build_tearsheet(t)
        logger.info("Test complete.")
