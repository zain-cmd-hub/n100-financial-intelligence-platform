from typing import Optional
import math

def safe_divide(numerator, denominator):
    """
    Safely divide two numbers.

    Returns None when denominator is
    None or zero.
    """

    if denominator is None:
        return None

    if denominator == 0:
        return None

    return numerator / denominator

def net_profit_margin(
    net_profit,
    sales
):
    """
    Net Profit Margin (%)

    Formula:
    Net Profit / Sales × 100
    """

    value = safe_divide(
        net_profit,
        sales
    )

    if value is None:
        return None

    return round(
        value * 100,
        2
    )

def operating_profit_margin(
    operating_profit,
    sales
):
    """
    Operating Profit Margin (%)
    """

    value = safe_divide(
        operating_profit,
        sales
    )

    if value is None:
        return None

    return round(
        value * 100,
        2
    )
def opm_cross_check(
    calculated_opm,
    source_opm,
    tolerance=1
):
    """
    Compare calculated OPM
    with source OPM.
    """

    if calculated_opm is None:
        return False

    if source_opm is None:
        return False

    difference = abs(
        calculated_opm -
        source_opm
    )

    return difference <= tolerance

def return_on_equity(
    net_profit,
    equity,
    reserves
):
    """
    ROE (%)

    Net Profit /
    (Equity + Reserves)
    ×100
    """

    capital = equity + reserves

    if capital <= 0:
        return None

    value = safe_divide(
        net_profit,
        capital
    )

    if value is None:
        return None

    return round(
        value * 100,
        2
    )

def return_on_capital_employed(
    operating_profit,
    interest,
    equity,
    reserves,
    borrowings
):
    """
    ROCE

    EBIT /
    Capital Employed
    """

    ebit = operating_profit + interest

    capital = (
        equity +
        reserves +
        borrowings
    )

    if capital <= 0:
        return None

    value = safe_divide(
        ebit,
        capital
    )

    if value is None:
        return None

    return round(
        value * 100,
        2
    )
def return_on_assets(
    net_profit,
    total_assets
):
    """
    ROA (%)
    """

    value = safe_divide(
        net_profit,
        total_assets
    )

    if value is None:
        return None

    return round(
        value * 100,
        2
    )

def debt_to_equity(
    borrowings,
    equity,
    reserves
):
    """
    Debt to Equity Ratio

    Formula:
    Borrowings /
    (Equity + Reserves)

    Rules:
    • Borrowings = 0 -> return 0
    • Capital <= 0 -> return None
    """

    if borrowings == 0:
        return 0

    capital = equity + reserves

    if capital <= 0:
        return None

    value = safe_divide(
        borrowings,
        capital
    )

    if value is None:
        return None

    return round(value, 2)

def high_leverage_flag(
    debt_equity,
    sector
):
    """
    High leverage warning.

    Ignore Financials sector.
    """

    if debt_equity is None:
        return False

    if sector is None:
        return debt_equity > 5

    if str(sector).lower() == "financials":
        return False

    return debt_equity > 5

def interest_coverage_ratio(
    operating_profit,
    other_income,
    interest
):
    """
    Interest Coverage Ratio

    (Operating Profit + Other Income)
/ Interest
    """

    if interest == 0:
        return None

    ebit = (
        operating_profit +
        other_income
    )

    value = safe_divide(
        ebit,
        interest
    )

    if value is None:
        return None

    return round(value, 2)

def interest_coverage_label(
    interest
):
    """
    Display label for debt free companies.
    """

    if interest == 0:
        return "Debt Free"

    return ""

def interest_coverage_warning(
    icr
):
    """
    Company unable to comfortably
    cover interest.
    """

    if icr is None:
        return False

    return icr < 1.5

def net_debt(
    borrowings,
    investments
):
    """
    Net Debt

    Borrowings -
    Investments
    """

    return round(
        borrowings -
        investments,
        2
    )

def asset_turnover(
    sales,
    total_assets
):
    """
    Asset Turnover

    Sales /
    Total Assets
    """

    value = safe_divide(
        sales,
        total_assets
    )

    if value is None:
        return None

    return round(value, 2)


def cagr_turnaround_flag(start_val, end_val):
    if start_val < 0 and end_val > 0:
        return True
    return False

def cagr_decline_to_loss_flag(start_val, end_val):
    if start_val > 0 and end_val < 0:
        return True
    return False

def calculate_cagr(start_val, end_val, years):
    if start_val <= 0 or end_val <= 0 or years <= 0:
        return None
    cagr = ((end_val / start_val) ** (1 / years) - 1) * 100
    return round(cagr, 2)

def cfo_quality_score(cfo_vals, pat_vals):
    if not cfo_vals or not pat_vals or len(cfo_vals) != len(pat_vals):
        return 0.0
    ratios_arr = []
    for cfo, pat in zip(cfo_vals, pat_vals):
        if pat > 0:
            ratios_arr.append(cfo / pat)
        elif pat <= 0 and cfo > 0:
            ratios_arr.append(2.0)
        else:
            ratios_arr.append(0.0)
    import numpy as np
    return float(np.mean(ratios_arr)) if ratios_arr else 0.0

