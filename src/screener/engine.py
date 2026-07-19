from pathlib import Path
import sqlite3
import pandas as pd
import yaml
try:
    from src.screener.presets import PRESETS
except ImportError:
    from presets import PRESETS


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

    def close(self):
        self.conn.close()

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

        # Keep only latest financial year for each company
        df = (
            df.sort_values(["company_id", "year"])
              .drop_duplicates(
                  subset="company_id",
                  keep="last"
              )
              .reset_index(drop=True)
        )

        print("=" * 60)
        print("MERGED DATA")
        print("=" * 60)
        print(f"Merged Records : {len(df)}")

        print("\nShape :", df.shape)

        return df

    # -------------------------------------------------
    # Apply Filters
    # -------------------------------------------------
    def apply_filters(self, df, filters=None, preset_name="custom"):

        df = df.copy()

        if filters is None:
            config = self.load_config()
            filters = config["filters"]

        def normalize(series):
            series = series.fillna(0)

            if series.max() == series.min():
                return series

            return (series - series.min()) / (series.max() - series.min())

        # ROE
        if filters.get("roe_min") is not None:
            df = df[df["return_on_equity_pct"] >= filters["roe_min"]]

        # Debt to Equity
        if filters.get("debt_to_equity_max") is not None:
            df["debt_to_equity"] = (
                df["debt_to_equity"]
                .replace({"Debt Free": 0})
            )

            df["debt_to_equity"] = pd.to_numeric(
                df["debt_to_equity"],
                errors="coerce"
            )

            sector_column = None
            for candidate in ["broad_sector", "sector_name", "sector", "industry"]:
                if candidate in df.columns:
                    sector_column = candidate
                    break

            if sector_column is not None:
                financial = (
                    df[sector_column]
                    .astype(str)
                    .str.strip()
                    .str.lower() == "financials"
                )
            else:
                financial = pd.Series(False, index=df.index)

            df = df[
                financial |
                (df["debt_to_equity"] <= filters["debt_to_equity_max"])
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
            df["interest_coverage"] = (
                df["interest_coverage"]
                .replace({"Debt Free": 999999})
            )

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
        roe = normalize(df["return_on_equity_pct"])
        opm = normalize(df["operating_profit_margin_pct"])
        at = normalize(df["asset_turnover"])
        ic = normalize(df["interest_coverage"])
        fcf = normalize(df["free_cash_flow_cr"].clip(lower=0))

        df["quality_score"] = (
            roe * 0.30 +
            opm * 0.25 +
            at * 0.15 +
            ic * 0.15 +
            fcf * 0.15
        ) * 100
        
        

        # -------------------------------------------------
        # Sort by Quality Score
        # -------------------------------------------------

        df = df.sort_values(
            by="quality_score",
            ascending=False
        )

        df = df.reset_index(drop=True)

        # -------------------------------------------------
        # Ranking
        # -------------------------------------------------

        df["rank"] = range(1, len(df) + 1)

        # -------------------------------------------------
        # Display Top Stocks
        # -------------------------------------------------
        print("\n" + "=" * 60)
        print(f"Preset : {preset_name.title()}")
        print(f"Companies Found : {len(df)}")
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

        print("\n" + "=" * 60)
        print("VALIDATION")
        print("=" * 60)

        print("Latest Year          :", df["year"].max())
        print("CSV Rows             :", len(df))
        print("Rows After Filtering :", len(df))
        print("Unique Companies     :", df["company_id"].nunique())

        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)

        file_name = f"{preset_name}_screener.csv"

        df.to_csv(
            output_dir / file_name,
            index=False
        )

        print("\nCSV Saved Successfully!")
        print(output_dir / file_name)

        return df

    # -------------------------------------------------
    # Run Preset Screener
    # -------------------------------------------------
    def run_preset(self, preset_name):

        preset_name = preset_name.lower()

        if preset_name not in PRESETS:
            print("\nInvalid Preset!")
            print("Available Presets:")
            for p in PRESETS:
                print("-", p)
            return None

        print("\n" + "=" * 60)
        print(f"RUNNING {preset_name.upper()} SCREENER")
        print("=" * 60)

        df = self.merge_data()

        result = self.apply_filters(
            df=df,
            filters=PRESETS[preset_name],
            preset_name=preset_name
        )

        return result


# -------------------------------------------------
# Main
# -------------------------------------------------
if __name__ == "__main__":

    engine = ScreenerEngine()

    print("=" * 60)
    print("AVAILABLE PRESETS")
    print("=" * 60)

    for preset in PRESETS.keys():
        print("-", preset)

    preset = input("\nEnter Preset : ").strip().lower()

    filtered_df = engine.run_preset(preset)

    if filtered_df is None:
        engine.close()
        exit()

    engine.close()