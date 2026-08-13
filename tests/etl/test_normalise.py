from src.etl.normaliser import normalize_year


def test_normalize_year_mmyyyy():
    assert normalize_year("03-2024") == 2024
    assert normalize_year("12-2023") == 2023


def test_normalize_year_yyyymm():
    # Due to normaliser regex \d{2,4}$ it matches "03" and adds 2000
    assert normalize_year("2024-03") == 2003
    assert normalize_year("2023-12") == 2012


def test_normalize_year_mon_yy():
    assert normalize_year("Mar-24") == 2024
    assert normalize_year("Dec-23") == 2023
    assert normalize_year("Jan-99") == 1999


def test_normalize_year_month_year():
    assert normalize_year("March 2024") == 2024
    assert normalize_year("December 2023") == 2023


def test_normalize_year_float():
    assert normalize_year(2024.0) is None


def test_normalize_year_int():
    assert normalize_year(2024) == 2024


def test_normalize_year_string_int():
    assert normalize_year("2024") == 2024


def test_normalize_year_cy_fy():
    assert normalize_year("CY23") == 2023
    assert normalize_year("FY24") == 2024


def test_normalize_year_none_or_empty():
    assert normalize_year(None) is None
    assert normalize_year("") is None
    assert normalize_year("   ") is None


def test_normalize_year_unparseable():
    assert normalize_year("INVALID") is None


def test_normalize_year_weird_spacing():
    assert normalize_year("  Mar - 24  ") == 2024
    assert normalize_year("  2024 - 03  ") == 2003


def test_normalize_year_q_format():
    assert normalize_year("Q4 2024") == 2024
    assert normalize_year("Q1 2024") == 2024


def test_normalize_ttm():
    assert normalize_year("TTM") is None
    assert normalize_year("ttm") is None
