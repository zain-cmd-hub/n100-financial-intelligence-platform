from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_valid_params():
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)

    # Check that all returned companies have ROE >= 15
    for company in data:
        # Check both possible keys returned by the API
        roe = company.get("return_on_equity_pct")
        if roe is None:
            roe = company.get("roe_percentage")

        if roe is not None:
            # If the API scaled it down (e.g. 52% as 0.52)
            if roe < 1 and roe > 0:
                assert roe * 100 >= 15
            else:
                assert roe >= 15


def test_screener_invalid_params():
    response = client.get("/api/v1/screener?min_roe=invalid")
    assert response.status_code in (400, 422)
