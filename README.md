# Nifty100 Financial Intelligence Platform

## Project Overview
The Nifty100 Financial Intelligence Platform is a comprehensive data engineering, analytics, and visualization solution for the top 100 companies on the National Stock Exchange (NSE). 
It processes 10+ years of historical financial data (P&L, Balance Sheet, Cash Flow), calculates key financial ratios, runs clustering algorithms (KMeans), generates PDF tearsheets, and serves everything via a high-performance FastAPI server to a Streamlit dashboard.

## System Requirements
- Python 3.10+
- SQLite3
- 2GB+ RAM

## Setup Instructions

1. **Clone the repository & create virtual environment:**
```bash
git clone https://github.com/zain-cmd-hub/n100-financial-intelligence-platform.git
cd n100-financial-intelligence-platform
python -m venv .venv
source .venv/Scripts/activate  # On Windows
```

2. **Install Dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

## Running Instructions

### 1. ETL Pipeline
To ingest Excel templates, run data quality checks, and populate the database:
```bash
python src/etl/loader.py
python src/etl/populate_financial_ratios.py
```

### 2. FastAPI Server
To start the backend API server on port 8000:
```bash
uvicorn src.api.main:app --port 8000 --reload
```
View the Swagger interactive documentation at: `http://localhost:8000/docs`

### 3. Streamlit Dashboard
To launch the user interface on port 8501:
```bash
streamlit run src/dashboard/app.py
```

### 4. Running the Test Suite
The project contains 70+ unit and integration tests across ETL, KPIs, Data Quality, and API endpoints. To run them and generate an HTML report:
```bash
pytest tests/ --html=reports/pytest_report.html -v
```

## Documentation
- The detailed 10-page user manual can be found at `docs/analyst_guide.pdf`.
- The OpenAPI specification is available at `docs/openapi.json`.
- Performance metrics and notes are located in `output/perf_notes.md`.
