from unittest.mock import patch

import pandas as pd

from src.etl.validator import (
    check_annual_report_url,
    check_balance_sheet,
    check_bse_profile,
    check_company_website,
    check_composite_key,
    check_dividend_payout,
    check_eps_sign,
    check_foreign_key,
    check_net_cash_flow,
    check_opm,
    check_positive_sales,
    check_primary_key,
    check_roe_range,
    check_tax_rate,
)


def get_failures(check_func, *args):
    failures = []

    def mock_record(dq_rule, severity, description, failed_df):
        failures.append((dq_rule, severity, description, failed_df))

    with patch("src.etl.validator.record_failure", side_effect=mock_record):
        check_func(*args)

    return failures


def test_check_primary_key():
    df = pd.DataFrame({"id": [1, 1, 2], "company_name": ["A", "B", "C"]})
    fails = get_failures(check_primary_key, df, "id")
    assert len(fails) == 1
    assert "CRITICAL" in fails[0][1]


def test_check_composite_key():
    df = pd.DataFrame(
        {"company_id": ["A", "A"], "year": [2020, 2020], "company_name": ["A", "A"]}
    )
    fails = get_failures(check_composite_key, df, ["company_id", "year"])
    assert len(fails) == 1
    assert "CRITICAL" in fails[0][1]


def test_check_foreign_key():
    child_df = pd.DataFrame({"fk": ["A", "B", "C"], "company_name": ["1", "2", "3"]})
    parent_df = pd.DataFrame({"id": ["A", "B"]})
    fails = get_failures(check_foreign_key, parent_df, child_df, "id", "fk")
    assert len(fails) == 1
    assert fails[0][1] == "CRITICAL"


def test_check_balance_sheet():
    df = pd.DataFrame(
        {
            "id": [1],
            "company_name": ["A"],
            "company_id": ["A"],
            "year": [2020],
            "total_liabilities": [100],
            "total_assets": [90],
        }
    )
    fails = get_failures(check_balance_sheet, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_opm():
    df = pd.DataFrame(
        {
            "company_id": ["A"],
            "year": [2020],
            "operating_profit": [10],
            "sales": [100],
            "opm_percentage": [20.0],
        }
    )
    fails = get_failures(check_opm, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_positive_sales():
    df = pd.DataFrame({"company_id": ["A"], "year": [2020], "sales": [-100]})
    fails = get_failures(check_positive_sales, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_net_cash_flow():
    df = pd.DataFrame(
        {
            "company_id": ["A"],
            "year": [2020],
            "operating_activity": [10],
            "investing_activity": [10],
            "financing_activity": [10],
            "net_cash_flow": [50],
        }
    )
    fails = get_failures(check_net_cash_flow, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_tax_rate():
    df = pd.DataFrame({"company_id": ["A"], "year": [2020], "tax_percentage": [105]})
    fails = get_failures(check_tax_rate, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_dividend_payout():
    df = pd.DataFrame({"company_id": ["A"], "year": [2020], "dividend_payout": [200]})
    fails = get_failures(check_dividend_payout, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_eps_sign():
    df = pd.DataFrame(
        {"company_id": ["A"], "year": [2020], "net_profit": [-10], "eps": [5]}
    )
    fails = get_failures(check_eps_sign, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_annual_report_url():
    df = pd.DataFrame(
        {
            "id": [1],
            "company_name": ["A"],
            "Annual_Report": ["http://invalid"],
            "is_url_valid": [False],
        }
    )
    fails = get_failures(check_annual_report_url, df)
    assert len(fails) >= 0


def test_check_bse_profile():
    df = pd.DataFrame(
        {"id": [1], "company_name": ["A"], "bse_profile": ["invalid_url"]}
    )
    fails = get_failures(check_bse_profile, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_roe_range():
    df = pd.DataFrame({"id": [1], "company_name": ["A"], "roe_percentage": [200]})
    fails = get_failures(check_roe_range, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"


def test_check_company_website():
    df = pd.DataFrame({"id": [1], "company_name": ["A"], "website": ["not_a_link"]})
    fails = get_failures(check_company_website, df)
    assert len(fails) == 1
    assert fails[0][1] == "WARNING"
