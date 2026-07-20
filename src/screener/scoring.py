import logging
from typing import Dict
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class CompositeScorer:
    """
    Calculates a composite score for companies based on various financial metrics.
    """

    WEIGHTS: Dict[str, float] = {
        "roe": 0.15,
        "roce": 0.10,
        "npm": 0.10,
        "fcf_cagr": 0.15,
        "cfo_pat": 0.10,
        "fcf_positive": 0.05,
        "revenue_cagr": 0.10,
        "pat_cagr": 0.10,
        "de_score": 0.10,
        "icr_score": 0.05
    }

    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the CompositeScorer with a copy of the dataframe.

        Args:
            dataframe (pd.DataFrame): The input dataframe containing company financials.
        """
        self.df = dataframe.copy()

    def winsorize(self, series: pd.Series) -> pd.Series:
        """
        Cap extreme values using P10 and P90 Winsorisation.

        Args:
            series (pd.Series): The pandas Series to winsorize.

        Returns:
            pd.Series: Winsorized pandas Series.
        """
        series = pd.to_numeric(series, errors="coerce")
        p10 = series.quantile(0.10)
        p90 = series.quantile(0.90)
        return series.clip(lower=p10, upper=p90)

    def normalize(self, series: pd.Series) -> pd.Series:
        """
        Normalize a metric to a 0–100 scale after Winsorisation.

        Args:
            series (pd.Series): The pandas Series to normalize.

        Returns:
            pd.Series: Normalized pandas Series on a 0-100 scale.
        """
        # Cap extreme values
        series = self.winsorize(series)

        # Fill missing values with median
        series = series.fillna(series.median())

        minimum = series.min()
        maximum = series.max()

        # Handle constant or invalid series
        if pd.isna(minimum) or pd.isna(maximum) or minimum == maximum:
            return pd.Series(50.0, index=series.index)

        # Scale between 0 and 100
        return ((series - minimum) / (maximum - minimum)) * 100

    def _calculate_company_cagr(self, value_column: str) -> pd.Series:
        """
        Compute CAGR per company using vectorized operations and align the result
        with the dataframe index.

        Args:
            value_column (str): The column name to calculate CAGR for.

        Returns:
            pd.Series: A pandas Series containing the CAGR values mapped to the original index.
        """
        if not {"company_id", "year", value_column}.issubset(self.df.columns):
            logger.warning(f"Missing columns for CAGR calculation on {value_column}.")
            return pd.Series(index=self.df.index, dtype="float64")

        working = self.df[["company_id", "year", value_column]].copy()
        working["year"] = pd.to_numeric(working["year"], errors="coerce")
        working[value_column] = pd.to_numeric(working[value_column], errors="coerce")

        working = working.dropna(subset=["company_id", "year", value_column])

        if working.empty:
            return pd.Series(index=self.df.index, dtype="float64")

        working = working.sort_values(["company_id", "year"])

        # Vectorized calculation
        groups = working.groupby("company_id")
        starts = groups[value_column].first()
        ends = groups[value_column].last()
        years = groups.size() - 1

        # Conditions for valid CAGR: years > 0, start > 0, end > 0
        valid_mask = (years > 0) & (starts > 0) & (ends > 0)

        cagrs = pd.Series(index=starts.index, dtype="float64")
        cagrs[valid_mask] = ((ends[valid_mask] / starts[valid_mask]) ** (1 / years[valid_mask]) - 1) * 100

        # Map back to original dataframe index via company_id
        result = self.df["company_id"].map(cagrs)
        return result

    def calculate_revenue_cagr(self) -> pd.Series:
        """Calculate Revenue CAGR for each company."""
        return self._calculate_company_cagr("sales")

    def calculate_pat_cagr(self) -> pd.Series:
        """Calculate PAT (Net Profit) CAGR for each company."""
        return self._calculate_company_cagr("net_profit")

    def calculate_fcf_cagr(self) -> pd.Series:
        """Calculate Free Cash Flow CAGR for each company."""
        return self._calculate_company_cagr("free_cash_flow_cr")

    def calculate_cfo_pat_ratio(self) -> pd.Series:
        """
        Calculate CFO to PAT ratio.

        Returns:
            pd.Series: A pandas Series containing the CFO to PAT ratio.
        """
        if not {"operating_activity", "net_profit"}.issubset(self.df.columns):
            logger.warning("Missing columns for CFO to PAT ratio calculation.")
            return pd.Series(index=self.df.index, dtype="float64")

        operating_activity = pd.to_numeric(self.df["operating_activity"], errors="coerce")
        net_profit = pd.to_numeric(self.df["net_profit"], errors="coerce")

        # Avoid division by zero warnings and deprecation warnings for replacing with pd.NA
        net_profit_safe = net_profit.replace({0: np.nan})
        ratio = operating_activity / net_profit_safe
        ratio = ratio.replace([np.inf, -np.inf], np.nan)

        return ratio

    def calculate_score(self) -> pd.DataFrame:
        """
        Calculate the Composite Quality Score (0–100) combining profitability,
        cash quality, growth, and leverage.

        Returns:
            pd.DataFrame: The original dataframe with added composite_score and intermediate metrics.
        """
        df = self.df.copy()

        try:
            df["revenue_cagr"] = self.calculate_revenue_cagr()
            df["pat_cagr"] = self.calculate_pat_cagr()
            df["free_cash_flow_cagr"] = self.calculate_fcf_cagr()
            df["cfo_pat_ratio"] = self.calculate_cfo_pat_ratio()

            # Profitability (35%)
            roe = self.normalize(df.get("return_on_equity_pct", pd.Series(0, index=df.index)))
            roce = self.normalize(df.get("roce_percentage", pd.Series(50.0, index=df.index)))
            npm = self.normalize(df.get("net_profit_margin_pct", pd.Series(0, index=df.index)))

            # Cash Quality (30%)
            fcf_cagr = self.normalize(df["free_cash_flow_cagr"])
            cfo_pat = self.normalize(df["cfo_pat_ratio"])

            fcf_positive = (
                (pd.to_numeric(df.get("free_cash_flow_cr", pd.Series(0, index=df.index)), errors="coerce") > 0)
                .astype(int) * 100
            )

            # Growth (20%)
            revenue_cagr = self.normalize(df["revenue_cagr"])
            pat_cagr = self.normalize(df["pat_cagr"])

            # Leverage (15%)
            debt = (
                pd.to_numeric(df.get("debt_to_equity", pd.Series(0, index=df.index)), errors="coerce")
                .fillna(0)
                .clip(lower=0)
            )
            de_score = 100 - self.normalize(debt)

            interest_val = df.get("interest_coverage", pd.Series("0", index=df.index)).replace({"Debt Free": 999999})
            interest = pd.to_numeric(interest_val, errors="coerce")
            icr_score = self.normalize(interest)

            df["composite_score"] = (
                roe * self.WEIGHTS["roe"] +
                roce * self.WEIGHTS["roce"] +
                npm * self.WEIGHTS["npm"] +
                fcf_cagr * self.WEIGHTS["fcf_cagr"] +
                cfo_pat * self.WEIGHTS["cfo_pat"] +
                fcf_positive * self.WEIGHTS["fcf_positive"] +
                revenue_cagr * self.WEIGHTS["revenue_cagr"] +
                pat_cagr * self.WEIGHTS["pat_cagr"] +
                de_score * self.WEIGHTS["de_score"] +
                icr_score * self.WEIGHTS["icr_score"]
            )
            logger.info("Composite score calculated successfully.")
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            df["composite_score"] = np.nan

        self.df = df
        return df