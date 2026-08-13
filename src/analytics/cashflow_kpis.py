import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.dashboard.utils.db import get_bs, get_cf, get_pl, get_ratios, get_screener_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"


def compute_cashflow_kpis():
    """Handles operations for compute_cashflow_kpis."""
    df_screener = get_screener_data()

    if df_screener.empty:
        logger.error("Failed to load screener data.")
        return

    results = []
    distress_alerts = []

    for _, row in df_screener.iterrows():
        cid = row["company_id"]
        sector = row["broad_sector"]

        cf = get_cf(cid)
        pl = get_pl(cid)
        bs = get_bs(cid)
        ratios = get_ratios(cid)

        # We need the most recent 5 years of data for CFO/PAT average
        cf_recent = cf.sort_values("year", ascending=False).head(5)
        pl_recent = pl.sort_values("year", ascending=False).head(5)

        # Merge to get CFO and PAT together
        cfo_pat = pd.merge(
            cf_recent[["year", "operating_activity"]],
            pl_recent[["year", "net_profit"]],
            on="year",
            how="inner",
        )

        cfo_vals = pd.to_numeric(cfo_pat["operating_activity"], errors="coerce").fillna(
            0
        )
        pat_vals = pd.to_numeric(cfo_pat["net_profit"], errors="coerce").fillna(0)

        # Calculate CFO/PAT ratio for each year
        ratios_arr = []
        for cfo, pat in zip(cfo_vals, pat_vals):
            if pat > 0:
                ratios_arr.append(cfo / pat)
            elif pat <= 0 and cfo > 0:
                # If PAT is negative but CFO is positive, it's very high quality (just an arbitrary cap)
                ratios_arr.append(2.0)
            else:
                # Both negative or CFO negative, PAT positive
                ratios_arr.append(0.0)

        cfo_quality_score = np.mean(ratios_arr) if ratios_arr else 0.0

        if cfo_quality_score > 1.0:
            cfo_quality_label = "High Quality"
        elif 0.5 <= cfo_quality_score <= 1.0:
            cfo_quality_label = "Moderate"
        else:
            cfo_quality_label = "Accrual Risk"

        # CapEx Intensity: abs(investing_activity) / sales x 100 for latest year
        latest_cf = cf.sort_values("year", ascending=False).head(1)
        latest_pl = pl.sort_values("year", ascending=False).head(1)

        inv_act = (
            pd.to_numeric(latest_cf["investing_activity"].values[0], errors="coerce")
            if not latest_cf.empty
            else 0
        )
        sales = (
            pd.to_numeric(latest_pl["sales"].values[0], errors="coerce")
            if not latest_pl.empty
            else 0
        )

        capex_intensity_pct = 0.0
        if sales and sales > 0:
            capex_intensity_pct = (abs(inv_act) / sales) * 100

        if capex_intensity_pct < 3:
            capex_label = "Asset Light"
        elif 3 <= capex_intensity_pct <= 8:
            capex_label = "Moderate"
        else:
            capex_label = "Capital Intensive"

        # Distress Signal: CFO < 0 AND CFF > 0 in latest year
        cfo_latest = (
            pd.to_numeric(latest_cf["operating_activity"].values[0], errors="coerce")
            if not latest_cf.empty
            else 0
        )
        cff_latest = (
            pd.to_numeric(latest_cf["financing_activity"].values[0], errors="coerce")
            if not latest_cf.empty
            else 0
        )
        net_profit_latest = (
            pd.to_numeric(latest_pl["net_profit"].values[0], errors="coerce")
            if not latest_pl.empty
            else 0
        )

        distress_flag = bool(cfo_latest < 0 and cff_latest > 0)

        if distress_flag:
            distress_alerts.append(
                {
                    "company_id": cid,
                    "CFO_value": cfo_latest,
                    "CFF_value": cff_latest,
                    "latest_net_profit": net_profit_latest,
                }
            )

        # Deleveraging flag: CFF < 0 AND borrowings declining year-over-year
        bs_recent = bs.sort_values("year", ascending=False).head(2)
        borrowings = (
            pd.to_numeric(bs_recent["borrowings"], errors="coerce").fillna(0).values
        )

        borrowings_declining = False
        if len(borrowings) == 2 and borrowings[0] < borrowings[1]:
            borrowings_declining = True

        deleveraging_flag = bool(cff_latest < 0 and borrowings_declining)

        # Capital Allocation Label
        de_latest = pd.to_numeric(
            str(row.get("debt_to_equity")).replace("Debt Free", "0"), errors="coerce"
        )
        if pd.isna(de_latest):
            de_latest = 0

        if capex_intensity_pct > 8 and de_latest > 0.5:
            capital_allocation_label = "Aggressive Growth"
        elif capex_intensity_pct < 3 and cfo_latest > 0:
            capital_allocation_label = "Cash Cow"
        elif cfo_latest > abs(inv_act):
            capital_allocation_label = "Self-Sustaining"
        else:
            capital_allocation_label = "External Dependent"

        # FCF Metrics
        fcf_cagr_5yr = pd.to_numeric(row.get("free_cash_flow_cagr"), errors="coerce")
        if pd.isna(fcf_cagr_5yr):
            fcf_cagr_5yr = 0.0

        latest_ratios = ratios.sort_values("year", ascending=False).head(1)
        fcf_latest = (
            pd.to_numeric(latest_ratios["free_cash_flow_cr"].values[0], errors="coerce")
            if not latest_ratios.empty
            else 0
        )

        fcf_conversion_pct = 0.0
        if net_profit_latest > 0:
            fcf_conversion_pct = (fcf_latest / net_profit_latest) * 100

        results.append(
            {
                "company_id": cid,
                "sector": sector,
                "cfo_quality_score": round(cfo_quality_score, 2),
                "cfo_quality_label": cfo_quality_label,
                "capex_intensity_pct": round(capex_intensity_pct, 2),
                "capex_label": capex_label,
                "fcf_cagr_5yr": round(fcf_cagr_5yr, 2),
                "fcf_conversion_pct": round(fcf_conversion_pct, 2),
                "distress_flag": distress_flag,
                "deleveraging_flag": deleveraging_flag,
                "capital_allocation_label": capital_allocation_label,
            }
        )

    # Save to Excel & CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df_results = pd.DataFrame(results)
    out_excel = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    df_results.to_excel(out_excel, index=False)
    logger.info(f"Saved {len(df_results)} company KPIs to {out_excel}")

    df_alerts = pd.DataFrame(distress_alerts)
    out_csv = OUTPUT_DIR / "distress_alerts.csv"
    if not df_alerts.empty:
        df_alerts.to_csv(out_csv, index=False)
        logger.warning(f"Saved {len(df_alerts)} distress alerts to {out_csv}")
    else:
        pd.DataFrame(
            columns=["company_id", "CFO_value", "CFF_value", "latest_net_profit"]
        ).to_csv(out_csv, index=False)
        logger.info(f"No distress alerts detected. Saved empty file to {out_csv}")


if __name__ == "__main__":
    compute_cashflow_kpis()
