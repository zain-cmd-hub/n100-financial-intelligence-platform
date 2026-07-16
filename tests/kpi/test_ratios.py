import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[2]
ANALYTICS_DIR = BASE_DIR / "src" / "analytics"

sys.path.insert(0, str(ANALYTICS_DIR))

from ratios import (
    net_profit_margin,
    operating_profit_margin,
    opm_cross_check,
    return_on_equity,
    debt_to_equity,
    interest_coverage_ratio,
    high_leverage_flag,
    asset_turnover
)


# ==========================================================
# 1. Net Profit Margin
# ==========================================================

def test_net_profit_margin():
    assert net_profit_margin(100, 1000) == 10.0


# ==========================================================
# 2. Zero Sales
# ==========================================================

def test_net_profit_margin_zero_sales():
    assert net_profit_margin(100, 0) is None


# ==========================================================
# 3. ROE Normal
# ==========================================================

def test_roe():
    assert return_on_equity(
        200,
        500,
        500
    ) == 20.0


# ==========================================================
# 4. Negative Equity
# ==========================================================

def test_negative_equity():
    assert return_on_equity(
        100,
        -500,
        100
    ) is None


# ==========================================================
# 5. OPM Cross Check
# ==========================================================

def test_opm_cross_check():
    calculated = operating_profit_margin(
        250,
        1000
    )

    assert opm_cross_check(
        calculated,
        25
    )


# ==========================================================
# 6. Debt Free
# ==========================================================

def test_debt_free():
    assert debt_to_equity(
        0,
        100,
        200
    ) == 0


# ==========================================================
# 7. Interest Coverage
# ==========================================================

def test_interest_zero():
    assert interest_coverage_ratio(
        500,
        100,
        0
    ) is None


# ==========================================================
# 8. High Leverage
# ==========================================================

def test_high_leverage():

    ratio = debt_to_equity(
        1000,
        100,
        50
    )

    assert high_leverage_flag(
        ratio,
        "Industrials"
    )


# ==========================================================
# 9. Asset Turnover
# ==========================================================

def test_asset_turnover():

    assert asset_turnover(
        1000,
        500
    ) == 2.0