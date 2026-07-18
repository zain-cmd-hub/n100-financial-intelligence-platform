from pathlib import Path
import sqlite3
import pandas as pd
import yaml

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"
CONFIG_FILE = BASE_DIR / "config" / "screener_config.yaml"


class ScreenerEngine:

    def __init__(self):
        self.conn = self.connect_db()

    # -------------------------------------------------
    # Database Connection
    # -------------------------------------------------
    def connect_db(self):
        return sqlite3.connect(DATABASE_FILE)

    # -------------------------------------------------
    # Load Config
    # -------------------------------------------------
    def load_config(self):
        with open(CONFIG_FILE, "r") as file:
            return yaml.safe_load(file)

    # -------------------------------------------------
    # Load Tables
    # -------------------------------------------------
    def load_data(self):

        financial_ratios = pd.read_sql(
            "SELECT * FROM financial_ratios",
            self.conn
        )

        market_cap = pd.read_sql(
            "SELECT * FROM market_cap",
            self.conn
        )

        sectors = pd.read_sql(
            "SELECT * FROM sectors",
            self.conn
        )

        companies = pd.read_sql(
            "SELECT * FROM companies",
            self.conn
        )

        return financial_ratios, market_cap, sectors, companies

    # -------------------------------------------------
    # Fix Data Types
    # -------------------------------------------------
    def fix_data_types(self, financial_ratios, market_cap, sectors, companies):

        financial_ratios["company_id"] = financial_ratios["company_id"].astype(str)
        market_cap["company_id"] = market_cap["company_id"].astype(str)
        sectors["company_id"] = sectors["company_id"].astype(str)
        companies["id"] = companies["id"].astype(str)

        # Convert "Mar 2022" -> 2022
        financial_ratios["year"] = (
            financial_ratios["year"]
            .astype(str)
            .str.extract(r"(\d{4})", expand=False)
        )

        financial_ratios = financial_ratios.dropna(subset=["year"])
        financial_ratios["year"] = financial_ratios["year"].astype(int)

        market_cap["year"] = market_cap["year"].astype(int)

        return financial_ratios, market_cap, sectors, companies

    # -------------------------------------------------
    # Merge Data
    # -------------------------------------------------
    def merge_data(self):

        financial_ratios, market_cap, sectors, companies = self.load_data()

        financial_ratios, market_cap, sectors, companies = self.fix_data_types(
            financial_ratios,
            market_cap,
            sectors,
            companies
        )

        # Merge Financial Ratios + Market Cap
        df = financial_ratios.merge(
            market_cap,
            on=["company_id", "year"],
            how="left",
            suffixes=("", "_market")
        )

        # Merge Sector
        df = df.merge(
            sectors,
            on="company_id",
            how="left"
        )

        # Merge Company Details
        df = df.merge(
            companies,
            left_on="company_id",
            right_on="id",
            how="left",
            suffixes=("", "_company")
        )

        print("=" * 60)
        print("MERGED DATA")
        print("=" * 60)
        print(df.head())

        print("\nShape :", df.shape)

        return df

    # -------------------------------------------------
    # Apply Filters
    # -------------------------------------------------
    def apply_filters(self, df):

        config = self.load_config()
        filters = config["filters"]

        # ROE
        if filters.get("roe_min") is not None:
            df = df[df["return_on_equity_pct"] >= filters["roe_min"]]

        # Debt to Equity
        if filters.get("debt_to_equity_max") is not None:
            df["debt_to_equity"] = pd.to_numeric(
                df["debt_to_equity"],
                errors="coerce"
            )

            df = df[
                df["debt_to_equity"] <= filters["debt_to_equity_max"]
            ]

        # Free Cash Flow
        if filters.get("free_cash_flow_min") is not None:
            df = df[
                df["free_cash_flow_cr"] >= filters["free_cash_flow_min"]
            ]

        # Operating Profit Margin
        if filters.get("operating_profit_margin_min") is not None:
            df = df[
                df["operating_profit_margin_pct"] >=
                filters["operating_profit_margin_min"]
            ]

        # PE
        if filters.get("pe_max") is not None:
            df = df[df["pe_ratio"] <= filters["pe_max"]]

        # PB
        if filters.get("pb_max") is not None:
            df = df[df["pb_ratio"] <= filters["pb_max"]]

        # Dividend Yield
        if filters.get("dividend_yield_min") is not None:
            df = df[
                df["dividend_yield_pct"] >=
                filters["dividend_yield_min"]
            ]

        # Interest Coverage
        if filters.get("interest_coverage_min") is not None:

            df["interest_coverage"] = pd.to_numeric(
                df["interest_coverage"],
                errors="coerce"
            )

            df = df[
                df["interest_coverage"] >=
                filters["interest_coverage_min"]
            ]

        # Market Cap
        if filters.get("market_cap_min") is not None:
            df = df[
                df["market_cap_crore"] >=
                filters["market_cap_min"]
            ]

        # Asset Turnover
        if filters.get("asset_turnover_min") is not None:
            df = df[
                df["asset_turnover"] >=
                filters["asset_turnover_min"]
            ]

        # -------------------------------------------------
        # Quality Score
        # -------------------------------------------------
        df["quality_score"] = (
            df["return_on_equity_pct"].fillna(0) * 0.40
            + df["operating_profit_margin_pct"].fillna(0) * 0.30
            + df["asset_turnover"].fillna(0) * 0.30
        )

        # -------------------------------------------------
        # Sort by Quality Score
        # -------------------------------------------------

        df = df.sort_values(
            by="quality_score",
            ascending=False
        )

        # -------------------------------------------------
        # Ranking
        # -------------------------------------------------

        df["rank"] = range(1, len(df) + 1)

        # -------------------------------------------------
        # Display Top Stocks
        # -------------------------------------------------
        print("\n" + "=" * 60)
        print("TOP SCREENED STOCKS")
        print("=" * 60)

        print(
            df[
                [
                    "rank",
                    "company_name",
                    "quality_score",
                    "return_on_equity_pct",
                    "operating_profit_margin_pct",
                    "asset_turnover",
                    "pe_ratio"
                ]
            ].head(10)
        )

        print("\nFiltered Shape :", df.shape)

        return df


# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":

    engine = ScreenerEngine()

    merged_df = engine.merge_data()

    filtered_df = engine.apply_filters(merged_df)