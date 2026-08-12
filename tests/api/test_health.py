import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    
    expected_tables = [
        "companies", "profit_loss", "balance_sheet", "cash_flow", 
        "financial_ratios", "market_data", "shareholding", 
        "price_history", "documents", "peer_percentiles"
    ]
    
    counts = data["db_row_counts"]
    for table in expected_tables:
        assert table in counts
