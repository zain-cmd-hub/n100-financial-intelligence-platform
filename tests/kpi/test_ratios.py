from src.analytics.ratios import (
    cagr_decline_to_loss_flag,
    cagr_turnaround_flag,
    calculate_cagr,
    cfo_quality_score,
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    opm_cross_check,
    return_on_equity,
)


def test_roe_positive_equity():
    # Net Profit = 100, Equity = 200, Reserves = 300 -> Cap = 500
    assert return_on_equity(100, 200, 300) == 20.0


def test_roe_negative_equity():
    # Cap = 100 + (-200) = -100 -> Returns None
    assert return_on_equity(100, 100, -200) is None


def test_roe_zero_profit():
    assert return_on_equity(0, 100, 100) == 0.0


def test_roe_zero_capital():
    assert return_on_equity(100, 0, 0) is None


def test_de_debt_free():
    assert debt_to_equity(0, 100, 100) == 0


def test_de_normal():
    # 50 / 100 = 0.5
    assert debt_to_equity(50, 50, 50) == 0.5


def test_de_negative_equity():
    assert debt_to_equity(100, 50, -100) is None


def test_icr_normal():
    # OP = 100, Other = 20, Int = 10 -> 120 / 10 = 12.0
    assert interest_coverage_ratio(100, 20, 10) == 12.0


def test_icr_zero_interest():
    assert interest_coverage_ratio(100, 20, 0) is None


def test_high_leverage_non_financial():
    assert high_leverage_flag(5.1, "Technology") is True
    assert high_leverage_flag(4.9, "Technology") is False


def test_high_leverage_financial():
    assert high_leverage_flag(6.0, "Financials") is False


def test_cagr_turnaround_flag():
    assert cagr_turnaround_flag(-10, 20) is True
    assert cagr_turnaround_flag(10, 20) is False


def test_cagr_decline_to_loss_flag():
    assert cagr_decline_to_loss_flag(10, -5) is True
    assert cagr_decline_to_loss_flag(10, 5) is False


def test_normal_cagr_calculation():
    # 100 to 121 in 2 years = 10%
    assert calculate_cagr(100, 121, 2) == 10.0


def test_cagr_invalid_values():
    assert calculate_cagr(-10, 100, 5) is None
    assert calculate_cagr(100, -10, 5) is None
    assert calculate_cagr(100, 200, 0) is None


def test_opm_cross_check_divergence():
    assert opm_cross_check(15.0, 15.5) is True
    assert opm_cross_check(15.0, 17.0) is False
    assert opm_cross_check(None, 15.0) is False


def test_cfo_quality_score_all_positive():
    assert cfo_quality_score([100, 150], [50, 100]) == 1.75  # (2.0 + 1.5) / 2


def test_cfo_quality_score_pat_negative_cfo_positive():
    assert cfo_quality_score([100], [-50]) == 2.0


def test_cfo_quality_score_both_negative():
    assert cfo_quality_score([-100], [-50]) == 0.0


def test_cfo_quality_score_empty():
    assert cfo_quality_score([], []) == 0.0
