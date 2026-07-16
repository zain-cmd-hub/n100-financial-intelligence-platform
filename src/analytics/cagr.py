from typing import Optional
import math

# ==========================================================
# CAGR FLAGS
# ==========================================================

NORMAL = "NORMAL"
TURNAROUND = "TURNAROUND"
DECLINE_TO_LOSS = "DECLINE_TO_LOSS"
BOTH_NEGATIVE = "BOTH_NEGATIVE"
ZERO_BASE = "ZERO_BASE"
INSUFFICIENT = "INSUFFICIENT"


# ==========================================================
# SAFE CAGR
# ==========================================================

def safe_cagr(start_value, end_value, years):
    """
    CAGR Formula

    ((End / Start)^(1 / Years) - 1) * 100

    Returns None if CAGR cannot be computed.
    """

    if years is None or years <= 0:
        return None

    if start_value is None or end_value is None:
        return None

    if start_value <= 0:
        return None

    if end_value <= 0:
        return None

    value = (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100

    return round(value, 2)


# ==========================================================
# CAGR ENGINE
# ==========================================================

def calculate_cagr(start_value, end_value, years):
    """
    Returns:
        (cagr_value, flag)
    """

    # Invalid years
    if years is None or years <= 0:
        return None, INSUFFICIENT

    # Missing values
    if start_value is None or end_value is None:
        return None, INSUFFICIENT

    # Zero base
    if start_value == 0:
        return None, ZERO_BASE

    # Turnaround
    if start_value < 0 and end_value > 0:
        return None, TURNAROUND

    # Decline to loss
    if start_value > 0 and end_value < 0:
        return None, DECLINE_TO_LOSS

    # Both negative
    if start_value < 0 and end_value < 0:
        return None, BOTH_NEGATIVE

    # Normal CAGR
    value = safe_cagr(
        start_value,
        end_value,
        years
    )

    return value, NORMAL


# ==========================================================
# GENERIC WRAPPERS
# ==========================================================

def revenue_cagr(start_sales, end_sales, years):
    return calculate_cagr(
        start_sales,
        end_sales,
        years
    )


def profit_cagr(start_profit, end_profit, years):
    return calculate_cagr(
        start_profit,
        end_profit,
        years
    )


def eps_cagr(start_eps, end_eps, years):
    return calculate_cagr(
        start_eps,
        end_eps,
        years
    )


# ==========================================================
# REVENUE CAGR
# ==========================================================

def revenue_cagr_3yr(start, end):
    return revenue_cagr(start, end, 3)


def revenue_cagr_5yr(start, end):
    return revenue_cagr(start, end, 5)


def revenue_cagr_10yr(start, end):
    return revenue_cagr(start, end, 10)


# ==========================================================
# PAT CAGR
# ==========================================================

def pat_cagr_3yr(start, end):
    return profit_cagr(start, end, 3)


def pat_cagr_5yr(start, end):
    return profit_cagr(start, end, 5)


def pat_cagr_10yr(start, end):
    return profit_cagr(start, end, 10)


# ==========================================================
# EPS CAGR
# ==========================================================

def eps_cagr_3yr(start, end):
    return eps_cagr(start, end, 3)


def eps_cagr_5yr(start, end):
    return eps_cagr(start, end, 5)


def eps_cagr_10yr(start, end):
    return eps_cagr(start, end, 10)