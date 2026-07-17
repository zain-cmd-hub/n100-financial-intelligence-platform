from src.analytics.cashflow_kpis import *


def test_fcf():
    assert free_cash_flow(1000, 200) == 800


def test_fcf_conversion():
    assert fcf_conversion(800, 400) == 2.0


def test_cfo_quality():
    assert cfo_quality(1000, 500) == 2.0


def test_capex():
    assert capex_intensity(200, 1000) == 0.2


def test_pattern():
    assert capital_allocation_pattern(1000, 200, debt_change=-100) == "Debt Reduction"