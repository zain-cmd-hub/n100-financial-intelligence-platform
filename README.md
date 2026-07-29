# Nifty 100 Financial Intelligence Platform

A full-stack, 8-screen Streamlit Dashboard providing deep financial analytics and valuation metrics for the Nifty 100 ecosystem.

## 🚀 How to Run the Dashboard

1. **Activate the Virtual Environment:**
   ```bash
   .venv\Scripts\activate
   ```
2. **Launch Streamlit:**
   ```bash
   streamlit run src/dashboard/app.py
   ```
3. The dashboard will automatically open in your browser at `http://localhost:8501`.

---

## 🖥️ Screen Breakdown (Sprint 4)

### 1. Home Dashboard (`01_home.py`)
- High-level KPIs (Average ROE, Median P/E, Total Companies, etc.).
- A Plotly Donut chart displaying the breakdown of Nifty 100 companies by Sector.
- Top-5 Quality Companies leaderboard based on the proprietary Composite Score.

### 2. Company Profile (`02_profile.py`)
- Instant Text-search dropdown for any company or ticker.
- Rapid (< 3s) load time with `@st.cache_data`.
- 10-year Bar (Revenue/PAT) and dual-axis Line charts (ROE/ROCE).
- Automated Pros & Cons badges based on algorithmic thresholds.

### 3. Advanced Screener (`03_screener.py`)
- 10 interactive metric sliders to filter the universe.
- **6 Preset Modes:** Quality, Value, Growth, Dividend, Debt-Free, and Turnaround. Clicking these instantly configures all 10 sliders.
- Real-time CSV Export capability.

### 4. Peer Comparison (`04_peers.py`)
- Compare companies within 11 distinct Peer Groups.
- Multi-dimensional Radar Chart (using `plotly.graph_objects.Scatterpolar`) analyzing 8 core metrics.
- Side-by-side KPI table with the Sector Benchmark highlighted.

### 5. Trend Analysis (`05_trends.py`)
- Overlay up to 3 custom metrics (Revenue, Net Profit, EPS, FCF) on a 10-year timeline.
- Dynamic YoY % change annotations directly calculated and plotted on each data point.

### 6. Sector Deep-Dive (`06_sectors.py`)
- Macro Plotly Bubble Chart (X=Revenue, Y=ROE, Size=Market Cap, Color=Sub-Sector).
- Sub-sector median KPI breakdown via a grouped bar chart.

### 7. Capital Allocation Map (`07_capital.py`)
- 92 companies algorithmically categorized into 8 Heuristic Capital Patterns (e.g., *Dividend Kings*, *Asset-Light Compounders*).
- Interactive Plotly Treemap sized by Market Cap for deep drill-down analytics.

### 8. Annual Reports Archive (`08_reports.py`)
- Direct links to BSE PDF Annual Reports (2019 - 2024).
- Built-in live URL verifier (using Python `requests`): Alerts the user with a red `[Report Unavailable]` badge if the BSE server returns a 404 error.

---

## 🔍 Valuation Engine (`src/analytics/valuation.py`)
A standalone analytics engine processing market cap and financial data to flag companies as Overvalued or Undervalued.

**Outputs generated:**
- `output/valuation_summary.xlsx` (Full set of 92 companies with FCF Yield and Sector Medians)
- `output/valuation_flags.csv` (Filtered list of companies marked **Caution** or **Discount**)

---

## 📘 Sprint 4 Retrospective

- **UX Decisions:** Implemented Streamlit's `st.session_state` heavily in the Screener screen to ensure the 6 Preset buttons could programmatically override the 10 manual sliders without causing race conditions.
- **Data Edge Cases:** Many tables contained the string `"Debt Free"` within numeric columns (like `debt_to_equity`). We successfully integrated `pd.to_numeric(df[col].replace("Debt Free", 0), errors='coerce')` globally to prevent mathematical crashes. Missing metrics (`NaN`) are safely cast to `"N/A"` in the UI.
- **Performance Findings:** By globally wrapping our SQLite reads in `@st.cache_data(ttl=600)`, we reduced individual screen load times from ~4.5s down to <0.3s on consecutive loads.
