import os
import sys
from pathlib import Path
import pandas as pd
import traceback

# Ensure src is in the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.screener.engine import ScreenerEngine
from src.screener.scoring import CompositeScorer

def test_engine_initialization():
    print("Running test_engine_initialization...")
    with ScreenerEngine() as engine:
        assert engine.conn is not None
    print("PASS: test_engine_initialization")

def test_load_config():
    print("Running test_load_config...")
    with ScreenerEngine() as engine:
        config = engine.load_config()
        assert isinstance(config, dict)
        assert "filters" in config or not config
    print("PASS: test_load_config")

def test_load_and_merge_data():
    print("Running test_load_and_merge_data...")
    with ScreenerEngine() as engine:
        df = engine.merge_data()
        assert not df.empty, "Merged dataframe should not be empty"
        assert "company_id" in df.columns
        assert "year" in df.columns
        assert "sales" in df.columns
        assert "net_profit" in df.columns
    print("PASS: test_load_and_merge_data")

def test_composite_scorer_cagr_vectorization():
    print("Running test_composite_scorer_cagr_vectorization...")
    data = {
        "company_id": ["A", "A", "A", "B", "B", "B"],
        "year": [2020, 2021, 2022, 2020, 2021, 2022],
        "sales": [100, 110, 121, 50, 100, 200],  # A: 10% CAGR, B: 100% CAGR
        "net_profit": [10, 11, 12.1, 5, 10, 20],
        "free_cash_flow_cr": [5, 6, 7, 2, 4, 8],
        "operating_activity": [15, 16, 17, 10, 15, 25],
        "return_on_equity_pct": [15, 16, 17, 20, 25, 30],
        "roce_percentage": [10, 11, 12, 15, 18, 20],
        "net_profit_margin_pct": [10, 10, 10, 10, 10, 10],
        "debt_to_equity": [0.5, 0.4, 0.3, 1.0, 0.8, 0.5],
        "interest_coverage": [5, 6, 7, 2, 3, 4]
    }
    df = pd.DataFrame(data)
    scorer = CompositeScorer(df)
    
    scored_df = scorer.calculate_score()
    
    assert "revenue_cagr" in scored_df.columns
    assert "composite_score" in scored_df.columns
    
    cagr_a = scored_df.loc[scored_df["company_id"] == "A", "revenue_cagr"].iloc[0]
    cagr_b = scored_df.loc[scored_df["company_id"] == "B", "revenue_cagr"].iloc[0]
    
    assert 9.9 < cagr_a < 10.1, f"Expected ~10, got {cagr_a}"
    assert 99.9 < cagr_b < 100.1, f"Expected ~100, got {cagr_b}"
    print("PASS: test_composite_scorer_cagr_vectorization")

def test_preset_execution():
    print("Running test_preset_execution...")
    with ScreenerEngine() as engine:
        result = engine.run_preset("growth")
        assert result is not None
        assert not result.empty
        assert "composite_score" in result.columns
        assert "rank" in result.columns
        assert len(result) == result["company_id"].nunique()
    print("PASS: test_preset_execution")

def test_all_presets():
    print("Running test_all_presets...")
    presets = ["growth", "value", "quality", "dividend"]
    with ScreenerEngine() as engine:
        for preset in presets:
            print(f"  -> Testing {preset}...")
            result = engine.run_preset(preset)
            assert result is not None
            assert not result.empty
    print("PASS: test_all_presets")

if __name__ == "__main__":
    try:
        test_engine_initialization()
        test_load_config()
        test_load_and_merge_data()
        test_composite_scorer_cagr_vectorization()
        test_preset_execution()
        test_all_presets()
        print("\nALL TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)
