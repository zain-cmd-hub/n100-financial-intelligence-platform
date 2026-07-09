import re
import pandas as pd


def normalize_ticker(ticker):
    """
    Normalize company ticker symbols.
    Example:
    ' tcs ' -> 'TCS'
    """

    if pd.isna(ticker):
        return None

    return str(ticker).strip().upper()


def normalize_year(year):
    """
    Normalize financial year values.

    Examples:
    Mar-24   -> 2024
    Mar-2023 -> 2023
    2022     -> 2022
    """

    if pd.isna(year):
        return None

    year = str(year).strip()

    # Find year at the end of the string
    match = re.search(r'(\d{2,4})$', year)

    if match:
        yr = match.group(1)

        if len(yr) == 2:
            return int("20" + yr)

        return int(yr)

    return None

