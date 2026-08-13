.PHONY: load ratios test report dashboard api clean

load:
	python src/etl/loader.py

ratios:
	python src/etl/populate_financial_ratios.py

test:
	pytest tests/ --html=reports/pytest_report.html

report:
	python src/reports/tearsheet.py
	python src/reports/sector_report.py
	python src/reports/portfolio_summary.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	uvicorn src.api.main:app --port 8000

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +