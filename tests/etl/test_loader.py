import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.etl.loader import clean_column_names, clean_text_columns, normalize_company_ids

def test_clean_column_names():
    df = pd.DataFrame(columns=["  Hello World  ", "Test@Column%", "Valid_Col"])
    df = clean_column_names(df)
    assert list(df.columns) == ["hello_world", "test@column%", "valid_col"]

def test_clean_column_names_empty():
    df = pd.DataFrame()
    df = clean_column_names(df)
    assert list(df.columns) == []

def test_clean_text_columns():
    df = pd.DataFrame({"text_col": ["  val  ", "val2\n"]})
    df = clean_text_columns(df)
    assert df["text_col"].tolist() == ["val", "val2"]
    
def test_normalize_company_ids():
    df = pd.DataFrame({"company_id": ["AGTL", "tcs"]})
    df = normalize_company_ids(df)
    assert df["company_id"].tolist() == ["ADANIGREEN", "TCS"]
    
def test_normalize_company_ids_missing_col():
    df = pd.DataFrame({"other_col": ["AGTL"]})
    df = normalize_company_ids(df)
    assert "company_id" not in df.columns

def test_load_excel_mocked():
    with patch("pandas.read_excel") as mock_read:
        with patch("pathlib.Path.exists", return_value=True):
            mock_read.return_value = pd.DataFrame({"col1": [1, 2]})
            from src.etl.loader import load_excel
            df = load_excel("fake_path.xlsx", header=0)
            assert len(df) == 2
            assert list(df.columns) == ["col1"]
        
def test_align_dataframe_to_table():
    from src.etl.loader import align_dataframe_to_table
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4], "col3": [5, 6]})
    mock_conn = MagicMock()
    with patch("src.etl.loader.get_table_columns", return_value=["col1", "col3"]):
        aligned = align_dataframe_to_table(mock_conn, df, "fake_table")
        assert list(aligned.columns) == ["col1", "col3"]
    
def test_remove_duplicate_primary_keys():
    from src.etl.loader import remove_duplicate_primary_keys
    df = pd.DataFrame({"id": [1, 1, 2], "val": ["a", "b", "c"]})
    with patch("src.etl.loader.get_table_columns", return_value=["id"]):
        dedup = remove_duplicate_primary_keys(df, "companies")
        assert len(dedup) == 2
    
def test_filter_invalid_foreign_keys():
    from src.etl.loader import filter_invalid_foreign_keys
    df = pd.DataFrame({"company_id": ["1", "2", "3"], "val": ["A", "B", "C"]})
    mock_conn = MagicMock()
    
    def fake_read_sql_query(*args, **kwargs):
        return pd.DataFrame({"id": ["1", "2"]})
        
    with patch("pandas.read_sql_query", side_effect=fake_read_sql_query):
        filtered = filter_invalid_foreign_keys(mock_conn, df, "test_table")
        assert len(filtered) == 2
