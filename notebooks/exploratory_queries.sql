-- ============================================================
-- NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM
-- Day 7 — Exploratory SQL Queries
-- ============================================================


-- ============================================================
-- QUERY 1
-- Total number of companies
-- Expected: 92
-- ============================================================

SELECT COUNT(*) AS total_companies
FROM companies;


-- ============================================================
-- QUERY 2
-- Companies by broad sector
-- ============================================================

SELECT
    broad_sector,
    COUNT(*) AS total_companies
FROM sectors
GROUP BY broad_sector
ORDER BY total_companies DESC;


-- ============================================================
-- QUERY 3
-- Top 10 companies by latest available sales
-- ============================================================

WITH latest_year AS (
    SELECT
        company_id,
        MAX(year) AS latest_year
    FROM profitandloss
    WHERE year <> 'TTM'
    GROUP BY company_id
)

SELECT
    c.company_name,
    p.company_id,
    p.year,
    p.sales
FROM profitandloss p

JOIN latest_year ly
    ON p.company_id = ly.company_id
    AND p.year = ly.latest_year

JOIN companies c
    ON p.company_id = c.id

ORDER BY p.sales DESC
LIMIT 10;


-- ============================================================
-- QUERY 4
-- Top 10 companies by latest available net profit
-- ============================================================

WITH latest_year AS (
    SELECT
        company_id,
        MAX(year) AS latest_year
    FROM profitandloss
    WHERE year <> 'TTM'
    GROUP BY company_id
)

SELECT
    c.company_name,
    p.company_id,
    p.year,
    p.net_profit
FROM profitandloss p

JOIN latest_year ly
    ON p.company_id = ly.company_id
    AND p.year = ly.latest_year

JOIN companies c
    ON p.company_id = c.id

ORDER BY p.net_profit DESC
LIMIT 10;


-- ============================================================
-- QUERY 5
-- Top 10 companies by ROE
-- ============================================================

SELECT
    id AS company_id,
    company_name,
    roe_percentage
FROM companies
WHERE roe_percentage IS NOT NULL
ORDER BY roe_percentage DESC
LIMIT 10;


-- ============================================================
-- QUERY 6
-- Companies with the highest market capitalization
-- using the latest available market-cap year
-- ============================================================

WITH latest_market_year AS (
    SELECT
        company_id,
        MAX(year) AS latest_year
    FROM market_cap
    GROUP BY company_id
)

SELECT
    c.company_name,
    m.company_id,
    m.year,
    m.market_cap_crore
FROM market_cap m

JOIN latest_market_year lm
    ON m.company_id = lm.company_id
    AND m.year = lm.latest_year

JOIN companies c
    ON m.company_id = c.id

ORDER BY m.market_cap_crore DESC
LIMIT 10;


-- ============================================================
-- QUERY 7
-- Companies with positive operating cash flow
-- in their latest available cash-flow year
-- ============================================================

WITH latest_cashflow_year AS (
    SELECT
        company_id,
        MAX(year) AS latest_year
    FROM cashflow
    WHERE year <> 'TTM'
    GROUP BY company_id
)

SELECT
    c.company_name,
    cf.company_id,
    cf.year,
    cf.operating_activity
FROM cashflow cf

JOIN latest_cashflow_year lc
    ON cf.company_id = lc.company_id
    AND cf.year = lc.latest_year

JOIN companies c
    ON cf.company_id = c.id

WHERE cf.operating_activity > 0

ORDER BY cf.operating_activity DESC;


-- ============================================================
-- QUERY 8
-- Average financial ratios by sector
-- ============================================================

SELECT
    s.broad_sector,

    ROUND(
        AVG(fr.return_on_equity_pct),
        2
    ) AS avg_roe,

    ROUND(
        AVG(fr.debt_to_equity),
        2
    ) AS avg_debt_to_equity,

    ROUND(
        AVG(fr.net_profit_margin_pct),
        2
    ) AS avg_net_profit_margin

FROM financial_ratios fr

JOIN sectors s
    ON fr.company_id = s.company_id

GROUP BY s.broad_sector

ORDER BY avg_roe DESC;


-- ============================================================
-- QUERY 9
-- Companies with less than 5 years of P&L data
-- ============================================================

SELECT
    c.id AS company_id,
    c.company_name,

    COUNT(
        DISTINCT p.year
    ) AS year_count

FROM companies c

LEFT JOIN profitandloss p
    ON c.id = p.company_id

GROUP BY
    c.id,
    c.company_name

HAVING COUNT(
    DISTINCT p.year
) < 5

ORDER BY year_count ASC;


-- ============================================================
-- QUERY 10
-- Latest stock price for every company
-- ============================================================

WITH latest_price_date AS (
    SELECT
        company_id,
        MAX(date) AS latest_date
    FROM stock_prices
    GROUP BY company_id
)

SELECT
    c.company_name,
    sp.company_id,
    sp.date,
    sp.close_price,
    sp.volume

FROM stock_prices sp

JOIN latest_price_date lp
    ON sp.company_id = lp.company_id
    AND sp.date = lp.latest_date

JOIN companies c
    ON sp.company_id = c.id

ORDER BY sp.close_price DESC;