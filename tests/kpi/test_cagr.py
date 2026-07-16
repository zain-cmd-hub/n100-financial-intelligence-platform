import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
ANALYTICS_DIR = BASE_DIR / "src" / "analytics"

sys.path.insert(0, str(ANALYTICS_DIR))

from cagr import (
    calculate_cagr,
    revenue_cagr_5yr,
    pat_cagr_5yr,
    eps_cagr_5yr,
    NORMAL,
    TURNAROUND,
    DECLINE_TO_LOSS,
    BOTH_NEGATIVE,
    ZERO_BASE,
    INSUFFICIENT,
)


# ==========================================================
# 1. Normal CAGR
# ==========================================================

def test_normal_cagr():
    value, flag = calculate_cagr(100, 200, 5)

    assert flag == NORMAL
    assert value is not None


# ==========================================================
# 2. Turnaround
# ==========================================================

def test_turnaround():
    value, flag = calculate_cagr(-100, 200, 5)

    assert value is None
    assert flag == TURNAROUND


# ==========================================================
# 3. Decline to Loss
# ==========================================================

def test_decline_to_loss():
    value, flag = calculate_cagr(100, -50, 5)

    assert value is None
    assert flag == DECLINE_TO_LOSS


# ==========================================================
# 4. Both Negative
# ==========================================================

def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 5)

    assert value is None
    assert flag == BOTH_NEGATIVE


# ==========================================================
# 5. Zero Base
# ==========================================================

def test_zero_base():
    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert flag == ZERO_BASE


# ==========================================================
# 6. Invalid Years
# ==========================================================

def test_invalid_years():
    value, flag = calculate_cagr(100, 200, 0)

    assert value is None
    assert flag == INSUFFICIENT


# ==========================================================
# 7. Revenue CAGR Wrapper
# ==========================================================

def test_revenue_cagr():
    value, flag = revenue_cagr_5yr(100, 200)

    assert flag == NORMAL
    assert value is not None


# ==========================================================
# 8. PAT CAGR Wrapper
# ==========================================================

def test_pat_cagr():
    value, flag = pat_cagr_5yr(200, 400)

    assert flag == NORMAL
    assert value is not None


# ==========================================================
# 9. EPS CAGR Wrapper
# ==========================================================

def test_eps_cagr():
    value, flag = eps_cagr_5yr(10, 20)

    assert flag == NORMAL
    assert value is not None


# ==========================================================
# 10. Missing Values
# ==========================================================

def test_missing_values():
    value, flag = calculate_cagr(None, 100, 5)

    assert value is None
    assert flag == INSUFFICIENT