import sys
from pathlib import Path

import pytest


# ============================================================
# IMPORT PROJECT MODULE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
ETL_DIR = BASE_DIR / "src" / "etl"

sys.path.insert(0, str(ETL_DIR))

from normaliser import normalize_ticker, normalize_year


# ============================================================
# NORMALIZE TICKER TESTS
# 20 TEST CASES
# ============================================================

@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("TCS", "TCS"),
        (" tcs ", "TCS"),
        ("tcs", "TCS"),
        ("HDFCBANK", "HDFCBANK"),
        (" hdfcbank ", "HDFCBANK"),
        ("reliance", "RELIANCE"),
        (" RELIANCE ", "RELIANCE"),
        ("INFY", "INFY"),
        (" infy", "INFY"),
        ("SBIN ", "SBIN"),
        ("icicibank", "ICICIBANK"),
        (" kotakbank ", "KOTAKBANK"),
        ("ADANIGREEN", "ADANIGREEN"),
        ("agTl", "ADANIGREEN"),
        (" AGTL ", "ADANIGREEN"),
        ("tatapower", "TATAPOWER"),
        (" techm ", "TECHM"),
        ("TVSMOTOR", "TVSMOTOR"),
        ("sunpharma", "SUNPHARMA"),
        (" bajfinance ", "BAJFINANCE"),
    ]
)
def test_normalize_ticker(
    input_value,
    expected
):
    """
    Test ticker normalization including:
    - uppercase conversion
    - whitespace removal
    - alias mapping
    """

    assert normalize_ticker(
        input_value
    ) == expected


# ============================================================
# NORMALIZE YEAR TESTS
# 20 TEST CASES
# ============================================================

@pytest.mark.parametrize(
    "input_value, expected",
    [
        ("Mar 2024", 2024),
        ("Mar 2023", 2023),
        ("Mar 2022", 2022),
        ("Mar 2021", 2021),
        ("Mar 2020", 2020),
        ("Dec 2012", 2012),
        ("Dec 2019", 2019),
        ("Mar-24", 2024),
        ("Mar-23", 2023),
        ("Mar-22", 2022),
        ("Mar-21", 2021),
        ("Mar-20", 2020),
        ("2024", 2024),
        ("2023", 2023),
        ("2022", 2022),
        (2021, 2021),
        (2020, 2020),
        ("  Mar 2018  ", 2018),
        ("TTM", None),
        (" ttm ", None),
    ]
)
def test_normalize_year(
    input_value,
    expected
):
    """
    Test financial year normalization.
    """

    assert normalize_year(
        input_value
    ) == expected


# ============================================================
# NULL VALUE TESTS
# ============================================================

def test_normalize_ticker_none():
    """
    None ticker should return None.
    """

    assert normalize_ticker(
        None
    ) is None


def test_normalize_year_none():
    """
    None year should return None.
    """

    assert normalize_year(
        None
    ) is None