"""
Preset Screeners
----------------
Reusable filter configurations for different investing strategies.
"""


# -------------------------------------------------
# Growth Screener
# -------------------------------------------------

GROWTH = {
    "roe_min": 18,
    "debt_to_equity_max": 0.5,
    "free_cash_flow_min": 0,
    "revenue_cagr_5y_min": 15,
    "pat_cagr_5y_min": 15,
    "eps_cagr_5y_min": 15,
    "operating_profit_margin_min": None,
    "pe_max": 40,
    "pb_max": None,
    "dividend_yield_min": None,
    "interest_coverage_min": None,
    "market_cap_min": None,
    "asset_turnover_min": None,
}


# -------------------------------------------------
# Value Screener
# -------------------------------------------------

VALUE = {
    "roe_min": 15,
    "debt_to_equity_max": 1,
    "free_cash_flow_min": 0,
    "revenue_cagr_5y_min": None,
    "pat_cagr_5y_min": None,
    "eps_cagr_5y_min": None,
    "operating_profit_margin_min": None,
    "pe_max": 20,
    "pb_max": 3,
    "dividend_yield_min": None,
    "interest_coverage_min": None,
    "market_cap_min": None,
    "asset_turnover_min": None,
}


# -------------------------------------------------
# Quality Screener
# -------------------------------------------------

QUALITY = {
    "roe_min": 20,
    "debt_to_equity_max": 0.5,
    "free_cash_flow_min": 0,
    "revenue_cagr_5y_min": None,
    "pat_cagr_5y_min": None,
    "eps_cagr_5y_min": None,
    "operating_profit_margin_min": 20,
    "pe_max": None,
    "pb_max": None,
    "dividend_yield_min": None,
    "interest_coverage_min": 5,
    "market_cap_min": None,
    "asset_turnover_min": None,
}


# -------------------------------------------------
# Dividend Screener
# -------------------------------------------------

DIVIDEND = {
    "roe_min": 15,
    "debt_to_equity_max": 1,
    "free_cash_flow_min": 0,
    "revenue_cagr_5y_min": None,
    "pat_cagr_5y_min": None,
    "eps_cagr_5y_min": None,
    "operating_profit_margin_min": None,
    "pe_max": None,
    "pb_max": None,
    "dividend_yield_min": 2,
    "interest_coverage_min": None,
    "market_cap_min": None,
    "asset_turnover_min": None,
}


# -------------------------------------------------
# Preset Registry
# -------------------------------------------------

PRESETS = {
    "growth": GROWTH,
    "value": VALUE,
    "quality": QUALITY,
    "dividend": DIVIDEND,
}