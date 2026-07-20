# Nifty100 Stock Screener

The Nifty100 Stock Screener is a production-grade algorithmic pipeline that evaluates companies within the Nifty100 index based on complex financial factors. It performs data extraction, validation, integration, composite scoring, and ranked filtering across multiple presets (Growth, Value, Quality, Dividend).

## Architecture

1. **Database Module (`db/`):** Contains raw SQLite financial data (`nifty100.db`).
2. **ETL Module (`src/etl/`):** Scripts to load and validate CSVs into the SQLite database.
3. **Screener Engine (`src/screener/engine.py`):** The core pipeline that connects to the database, extracts historical metrics, resolves duplication, merges tables using strict (`1:1` / `m:1`) cardinality, and filters stocks.
4. **Scoring Engine (`src/screener/scoring.py`):** Calculates normalized composite scores using a dynamic weighting system and vectorized CAGR computations over multi-year periods.

## Pipeline Flow

1. **Data Load:** `ScreenerEngine` opens a managed connection to `nifty100.db`.
2. **Sanitization:** Cleans duplicate entries across composite keys `(company_id, year)` to prevent cartesian explosion during joins.
3. **Merge Strategy:** Data is left-joined sequentially (`financial_ratios` → `market_cap` → `profit_loss` → `cash_flow` → `balance_sheet` → `sectors`).
4. **Scoring:** Missing data is handled via robust pandas operations. Outliers are normalized using Winsorization (P10/P90 capping). Advanced metrics like `CFO/PAT` and multi-year `Revenue/PAT/FCF CAGR` are computed efficiently via vectorized numpy structures.
5. **Ranking & Filtering:** Predefined filters (e.g. `pe_max`, `roe_min`) are applied via YAML config. Output is ranked by `composite_score` and exported as a CSV.

## Composite Score Formula

The Composite Score (0–100) is calculated using normalized values on a configurable weighted scale:

- **Profitability (35%):** ROE (15%), ROCE (10%), Net Profit Margin (10%)
- **Cash Quality (30%):** FCF CAGR (15%), CFO/PAT (10%), Positive FCF streak (5%)
- **Growth (20%):** Revenue CAGR (10%), PAT CAGR (10%)
- **Leverage (15%):** Debt-to-Equity inverted (10%), Interest Coverage Ratio (5%)

## Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/bluestock/nifty100-platform.git
   cd nifty100-platform
   ```

2. **Setup Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   ```

## Usage

### 1. Interactive CLI
Run the screener interactively to choose a preset (`growth`, `value`, `quality`, `dividend`). The resulting file will be saved in `output/`.
```bash
python -m src.screener.engine
```

### 2. Run Tests
Validate the system logic using the test suite.
```bash
python tests/test_screener.py
```
