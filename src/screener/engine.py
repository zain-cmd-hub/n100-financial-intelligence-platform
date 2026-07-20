import logging
import sqlite3
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

import pandas as pd
import yaml

try:
    from src.screener.presets import PRESETS
    from src.screener.scoring import CompositeScorer
except ImportError:
    from presets import PRESETS
    from scoring import CompositeScorer

# Configure root logger for the engine if not already configured
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# -------------------------------------------------
# Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_FILE = BASE_DIR / "db" / "nifty100.db"
CONFIG_FILE = BASE_DIR / "config" / "screener_config.yaml"


class ScreenerEngine:
    """
    Engine to load, merge, filter and rank Nifty100 financial data.
    """

    def __init__(self):
        """Initializes the ScreenerEngine and connects to the database."""
        self.conn: Optional[sqlite3.Connection] = None
        self.connect_db()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # -------------------------------------------------
    # Database Connection
    # -------------------------------------------------
    def connect_db(self) -> None:
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(DATABASE_FILE)
            logger.info("Connected to database successfully.")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            self.conn = None

    def close(self) -> None:
        """Close the database connection safely."""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                logger.info("Database connection closed.")
            except sqlite3.Error as e:
                logger.error(f"Error closing database: {e}")

    # -------------------------------------------------
    # Load Config
    # -------------------------------------------------
    def load_config(self) -> Dict[str, Any]:
        """
        Load filtering configuration from YAML file.
        
        Returns:
            Dict: Configuration parameters.
        """
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {CONFIG_FILE}")
            return {"filters": {}}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration YAML: {e}")
            return {"filters": {}}

    # -------------------------------------------------
    # Load Tables
    # -------------------------------------------------
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all necessary tables from the database.
        
        Returns:
            Tuple containing financial_ratios, profit_loss, cash_flow, 
            balance_sheet, market_cap, sectors, companies dataframes.
        """
        if not self.conn:
            logger.error("No database connection available.")
            empty_df = pd.DataFrame()
            return empty_df, empty_df, empty_df, empty_df, empty_df, empty_df, empty_df

        try:
            financial_ratios = pd.read_sql("SELECT * FROM financial_ratios", self.conn)
            profit_loss = pd.read_sql("SELECT * FROM profitandloss", self.conn)
            cash_flow = pd.read_sql("SELECT * FROM cashflow", self.conn)
            balance_sheet = pd.read_sql("SELECT * FROM balancesheet", self.conn)
            market_cap = pd.read_sql("SELECT * FROM market_cap", self.conn)
            sectors = pd.read_sql("SELECT * FROM sectors", self.conn)
            companies = pd.read_sql("SELECT * FROM companies", self.conn)
            
            logger.info("Successfully loaded all tables from database.")
            
            return (
                financial_ratios,
                profit_loss,
                cash_flow,
                balance_sheet,
                market_cap,
                sectors,
                companies
            )
        except pd.io.sql.DatabaseError as e:
            logger.error(f"Database query error during loading: {e}")
            empty_df = pd.DataFrame()
            return empty_df, empty_df, empty_df, empty_df, empty_df, empty_df, empty_df

    # -------------------------------------------------
    # Fix Data Types
    # -------------------------------------------------
    def fix_data_types(
        self,
        financial_ratios: pd.DataFrame,
        profit_loss: pd.DataFrame,
        cash_flow: pd.DataFrame,
        balance_sheet: pd.DataFrame,
        market_cap: pd.DataFrame,
        sectors: pd.DataFrame,
        companies: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Clean and standardize data types across loaded tables.
        """
        tables = [
            financial_ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
        ]

        for table in tables:
            if table.empty:
                continue
                
            if "company_id" in table.columns:
                table["company_id"] = table["company_id"].astype(str)

            if "year" in table.columns:
                table["year"] = (
                    table["year"]
                    .astype(str)
                    .str.extract(r"(\d{4})", expand=False)
                )
                table.dropna(subset=["year"], inplace=True)
                table["year"] = table["year"].astype(int)

        if not market_cap.empty:
            market_cap["company_id"] = market_cap["company_id"].astype(str)
            market_cap["year"] = pd.to_numeric(market_cap["year"], errors='coerce').fillna(0).astype(int)

        if not sectors.empty:
            sectors["company_id"] = sectors["company_id"].astype(str)
            
        if not companies.empty:
            companies["id"] = companies["id"].astype(str)

        return (
            financial_ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
            market_cap,
            sectors,
            companies,
        )

    # -------------------------------------------------
    # Merge Data
    # -------------------------------------------------
    def merge_data(self) -> pd.DataFrame:
        """
        Merge all tables into a unified dataframe.
        
        Returns:
            pd.DataFrame: Merged financial dataset.
        """
        (
            financial_ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
            market_cap,
            sectors,
            companies
        ) = self.load_data()

        if financial_ratios.empty:
            logger.error("Financial ratios table is empty. Aborting merge.")
            return pd.DataFrame()

        (
            financial_ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
            market_cap,
            sectors,
            companies,
        ) = self.fix_data_types(
            financial_ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
            market_cap,
            sectors,
            companies,
        )

        tables_to_check = {
            "financial_ratios": financial_ratios,
            "profit_loss": profit_loss,
            "cash_flow": cash_flow,
            "balance_sheet": balance_sheet,
            "market_cap": market_cap
        }
        
        for name, table in tables_to_check.items():
            if not table.empty and "year" in table.columns:
                dup_count = len(table) - len(table.groupby(["company_id", "year"]))
                if dup_count > 0:
                    logger.info(f"Fixed {dup_count} duplicate keys in {name}.")
                    tables_to_check[name] = table.groupby(["company_id", "year"], as_index=False).last()

        financial_ratios = tables_to_check["financial_ratios"]
        profit_loss = tables_to_check["profit_loss"]
        cash_flow = tables_to_check["cash_flow"]
        balance_sheet = tables_to_check["balance_sheet"]
        market_cap = tables_to_check["market_cap"]
        
        if not sectors.empty:
            sectors_dup = len(sectors) - len(sectors.groupby("company_id"))
            if sectors_dup > 0:
                logger.info(f"Fixed {sectors_dup} duplicate keys in sectors.")
                sectors = sectors.groupby("company_id", as_index=False).last()
                
        if not companies.empty:
            companies_dup = len(companies) - len(companies.groupby("id"))
            if companies_dup > 0:
                logger.info(f"Fixed {companies_dup} duplicate keys in companies.")
                companies = companies.groupby("id", as_index=False).last()
            
        try:
            # Merge Financial Ratios + Market Cap
            df = financial_ratios.merge(
                market_cap,
                on=["company_id", "year"],
                how="left",
                suffixes=("", "_market"),
                validate="1:1"
            )

            df = df.merge(
                profit_loss,
                on=["company_id", "year"],
                how="left",
                suffixes=("", "_pl"),
                validate="1:1"
            )

            df = df.merge(
                cash_flow,
                on=["company_id", "year"],
                how="left",
                suffixes=("", "_cf"),
                validate="1:1"
            )

            df = df.merge(
                balance_sheet,
                on=["company_id", "year"],
                how="left",
                suffixes=("", "_bs"),
                validate="1:1"
            )

            # Merge Sector
            df = df.merge(
                sectors,
                on="company_id",
                how="left",
                validate="m:1"
            )

            # Merge Company Details
            df = df.merge(
                companies,
                left_on="company_id",
                right_on="id",
                how="left",
                suffixes=("", "_company"),
                validate="m:1"
            )
            
            logger.info(f"Data merged successfully. Shape: {df.shape}")
            return df
            
        except pd.errors.MergeError as e:
            logger.error(f"Merge error occurred: {e}")
            return pd.DataFrame()

    # -------------------------------------------------
    # Apply Filters
    # -------------------------------------------------
    def apply_filters(
        self, 
        df: pd.DataFrame, 
        filters: Optional[Dict[str, float]] = None, 
        preset_name: str = "custom"
    ) -> pd.DataFrame:
        """
        Apply screening filters and rank stocks based on composite score.
        
        Args:
            df (pd.DataFrame): The merged dataframe.
            filters (Dict[str, float], optional): Dictionary of metric thresholds.
            preset_name (str): Name of the preset being applied.
            
        Returns:
            pd.DataFrame: Filtered and ranked dataframe.
        """
        if df.empty:
            logger.warning("Empty dataframe provided to apply_filters.")
            return df

        df = df.copy()

        if filters is None:
            config = self.load_config()
            filters = config.get("filters", {})

        scorer = CompositeScorer(df)
        df = scorer.calculate_score()

        # ROE
        if filters.get("roe_min") is not None:
            df = df[df["return_on_equity_pct"] >= filters["roe_min"]].copy()

        # Debt to Equity
        if filters.get("debt_to_equity_max") is not None:
            df["debt_to_equity"] = df["debt_to_equity"].replace({"Debt Free": 0})
            df["debt_to_equity"] = pd.to_numeric(df["debt_to_equity"], errors="coerce")

            sector_column = next((c for c in ["broad_sector", "sector_name", "sector", "industry"] if c in df.columns), None)
            
            if sector_column is not None:
                financial = df[sector_column].astype(str).str.strip().str.lower() == "financials"
            else:
                financial = pd.Series(False, index=df.index)

            df = df[financial | (df["debt_to_equity"] <= filters["debt_to_equity_max"])]

        # Free Cash Flow
        if filters.get("free_cash_flow_min") is not None:
            df = df[df["free_cash_flow_cr"] >= filters["free_cash_flow_min"]]

        # Operating Profit Margin
        if filters.get("operating_profit_margin_min") is not None:
            df = df[df["operating_profit_margin_pct"] >= filters["operating_profit_margin_min"]]

        # PE
        if filters.get("pe_max") is not None:
            df = df[df["pe_ratio"] <= filters["pe_max"]]

        # PB
        if filters.get("pb_max") is not None:
            df = df[df["pb_ratio"] <= filters["pb_max"]]

        # Dividend Yield
        if filters.get("dividend_yield_min") is not None:
            df = df[df["dividend_yield_pct"] >= filters["dividend_yield_min"]]

        # Interest Coverage
        if filters.get("interest_coverage_min") is not None:
            df["interest_coverage"] = df["interest_coverage"].replace({"Debt Free": 999999})
            df["interest_coverage"] = pd.to_numeric(df["interest_coverage"], errors="coerce")
            df = df[df["interest_coverage"] >= filters["interest_coverage_min"]]

        # Market Cap
        if filters.get("market_cap_min") is not None:
            df = df[df["market_cap_crore"] >= filters["market_cap_min"]]

        # Asset Turnover
        if filters.get("asset_turnover_min") is not None:
            df = df[df["asset_turnover"] >= filters["asset_turnover_min"]]

        df = (
            df.sort_values(["company_id", "year"])
              .drop_duplicates(subset="company_id", keep="last")
              .reset_index(drop=True)
        )

        # -------------------------------------------------
        # Sort by Composite Score
        # -------------------------------------------------
        df = df.sort_values(by="composite_score", ascending=False).reset_index(drop=True)

        # -------------------------------------------------
        # Ranking
        # -------------------------------------------------
        df["rank"] = range(1, len(df) + 1)

        # -------------------------------------------------
        # Display Top Stocks
        # -------------------------------------------------
        logger.info(f"Preset: {preset_name.title()} - Companies Found: {len(df)}")
        
        output_dir = BASE_DIR / "output"
        output_dir.mkdir(exist_ok=True)
        file_name = f"{preset_name}_screener.csv"
        
        try:
            df.to_csv(output_dir / file_name, index=False)
            logger.info(f"CSV Saved Successfully at {output_dir / file_name}")
        except OSError as e:
            logger.error(f"Failed to save CSV: {e}")

        return df

    # -------------------------------------------------
    # Run Preset Screener
    # -------------------------------------------------
    def run_preset(self, preset_name: str) -> Optional[pd.DataFrame]:
        """
        Execute the screener for a given preset.
        
        Args:
            preset_name (str): The preset configuration to apply.
            
        Returns:
            Optional[pd.DataFrame]: The resulting dataframe if successful, None otherwise.
        """
        preset_name = preset_name.strip().lower()

        if preset_name not in PRESETS:
            logger.error(f"Invalid Preset: {preset_name}")
            logger.info(f"Available Presets: {list(PRESETS.keys())}")
            return None

        logger.info(f"Running {preset_name.upper()} screener...")

        df = self.merge_data()
        
        if df.empty:
            logger.error("Merge returned an empty dataframe. Aborting filter application.")
            return None

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
    
    print("=" * 60)
    print("AVAILABLE PRESETS")
    print("=" * 60)

    for preset in PRESETS.keys():
        print("-", preset)

    try:
        preset_input = input("\nEnter Preset : ").strip().lower()
        with ScreenerEngine() as engine:
            filtered_df = engine.run_preset(preset_input)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")