"""
cashflow_kpis.py

Cash Flow KPI calculations for the NIFTY 100 Financial Intelligence Platform.
"""

from typing import Optional


def safe_divide(numerator: Optional[float], denominator: Optional[float]):
    """Safely divide two numbers."""
    if numerator is None or denominator is None:
        return None

    if denominator == 0:
        return None

    return round(numerator / denominator, 4)


# ----------------------------------------------------
# Free Cash Flow
# ----------------------------------------------------

def free_cash_flow(cfo, capex):
    """
    FCF = CFO - CapEx
    """
    if cfo is None or capex is None:
        return None

    return round(cfo - capex, 2)


# ----------------------------------------------------
# FCF Conversion
# ----------------------------------------------------

def fcf_conversion(fcf, pat):
    """
    FCF / PAT
    """
    return safe_divide(fcf, pat)


# ----------------------------------------------------
# CFO Quality
# ----------------------------------------------------

def cfo_quality(cfo, pat):
    """
    CFO / PAT
    """
    return safe_divide(cfo, pat)


# ----------------------------------------------------
# CapEx Intensity
# ----------------------------------------------------

def capex_intensity(capex, cfo):
    """
    CapEx / CFO
    """
    return safe_divide(capex, cfo)


# ----------------------------------------------------
# Capital Allocation Pattern
# ----------------------------------------------------

def capital_allocation_pattern(cfo, capex, debt_change=0, dividend=0):
    """
    Simple capital allocation classifier.
    """

    if cfo is None or capex is None:
        return "UNKNOWN"

    fcf = free_cash_flow(cfo, capex)

    if fcf is None:
        return "UNKNOWN"

    if fcf > 0 and debt_change < 0:
        return "Debt Reduction"

    if fcf > 0 and dividend > 0:
        return "Shareholder Returns"

    if fcf > 0 and capex > (0.5 * cfo):
        return "Growth Investment"

    if fcf < 0 and capex > cfo:
        return "Expansion Phase"

    if fcf < 0:
        return "Cash Burn"

    return "Balanced Allocation"