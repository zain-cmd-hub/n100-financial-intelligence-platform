import re
import pandas as pd


TICKER_ALIASES = {
    "AGTL": "ADANIGREEN",
}


def normalize_ticker(ticker):
    """
    Normalize company ticker symbols.
    """

    if pd.isna(ticker):
        return None

    ticker = str(ticker).strip().upper()

    return TICKER_ALIASES.get(ticker, ticker)


def normalize_year(year):
    """
    Normalize financial year values.
    """

    if pd.isna(year):
        return None

    year = str(year).strip()

    if year.upper() == "TTM":
        return None

    match = re.search(r"(\d{2,4})$", year)

    if match:
        yr = match.group(1)

        if len(yr) == 2:
            yr = int(yr)

            if yr <= 50:
                return 2000 + yr

            return 1900 + yr

        return int(yr)

    return None