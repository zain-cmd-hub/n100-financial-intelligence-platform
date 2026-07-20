# Nifty100 Financial Intelligence Platform (Data Analytics Internship Project)

> **Internship Details**
> - **Company:** Bluestock Fintech
> - **Role:** Data Analyst Intern
> - **Team Group:** 340FMBF
> - **Project Scope:** End-to-End Data Pipeline, ETL, Financial Analysis & Algorithmic Stock Screening

---

## Project Overview

This project was developed from the ground up during my internship at **Bluestock Fintech** to solve complex financial data evaluation challenges. It is a production-grade algorithmic pipeline that extracts raw financial data, validates and integrates it, and applies dynamic mathematical models to evaluate and screen companies within the Nifty100 index.

The screener is capable of classifying stocks across multiple pre-defined strategies: **Growth, Value, Quality, and Dividend**.

## Key Contributions & Technical Implementations

As a Data Analyst, my core responsibilities for this pipeline included:

1. **ETL (Extract, Transform, Load):** 
   - Engineered data ingestion scripts to securely load disparate financial CSVs (Balance sheets, P&L, Cash Flow) into a centralized SQLite schema.
   - Designed data validation protocols (`validator.py`) to prevent corrupt or incomplete data from polluting the database.
2. **Data Cleansing & Joining:** 
   - Resolved highly complex many-to-many (`m:m`) cartesian product issues during Pandas dataframe merges by implementing strict composite-key `(company_id, year)` aggregations and `1:1` cardinality validations.
3. **Financial Algorithm Design (Vectorization):**
   - Transformed inefficient iterative loops into highly performant, vectorized NumPy operations to calculate multi-year Compound Annual Growth Rates (CAGR) for Revenue, PAT, and Free Cash Flow.
   - Implemented P10/P90 Winsorization techniques to normalize severe financial outliers (mitigating statistical skewing).
4. **Production Readiness:** 
   - Configured robust Python `logging`, removed memory leaks using Python Context Managers, and structured the codebase to adhere to PEP-8 standards with comprehensive type hinting and Sphinx/Google docstrings.

---

## System Architecture

1. **Database Module (`db/`):** Contains the normalized SQLite financial data (`nifty100.db`).
2. **ETL Module (`src/etl/`):** Automated scripts and sanitization logic to bridge raw CSVs into the SQLite database.
3. **Screener Engine (`src/screener/engine.py`):** The operational core. It executes the database extraction, structural formatting, duplicate resolution, and left-joins sequential tables into a unified master dataset.
4. **Scoring Engine (`src/screener/scoring.py`):** The intelligence layer. It calculates complex metrics, normalizes them, and assigns dynamic weighted scores for final filtering and ranking.

---

## Composite Score Methodology

The engine calculates a definitive Composite Score (0–100) using normalized values on a strict weighted scale tailored for institutional-grade screening:

- **Profitability (35%):** ROE (15%), ROCE (10%), Net Profit Margin (10%)
- **Cash Quality (30%):** Free Cash Flow CAGR (15%), CFO/PAT Ratio (10%), Positive FCF Streak (5%)
- **Growth (20%):** Revenue CAGR (10%), Profit After Tax (PAT) CAGR (10%)
- **Leverage (15%):** Debt-to-Equity (Inverted) (10%), Interest Coverage Ratio (5%)

---

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

### 1. Interactive CLI Screener
Run the screener interactively to evaluate the Nifty100 universe against a specific strategy (`growth`, `value`, `quality`, `dividend`). The filtered, ranked dataset will be exported to the `output/` directory as a CSV.
```bash
python -m src.screener.engine
```

### 2. Run Automated Testing Suite
Validate the system logic, merge cardinality, and vectorized math algorithms using the test suite.
```bash
python tests/test_screener.py
```
