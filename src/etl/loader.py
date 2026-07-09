from pathlib import Path
import pandas as pd

from normaliser import normalize_ticker, normalize_year


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA = BASE_DIR / "data" / "raw"


def load_excel(file_path, header=0):
    """
    Load an Excel file safely.
    """

    try:
        df = pd.read_excel(file_path, header=header)

        print(f"Loaded: {Path(file_path).name}")
        print(f"Rows: {df.shape[0]}")
        print(f"Columns: {df.shape[1]}")

        return df

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def load_all_files():
    """
    Load all datasets from data/raw.
    """

    datasets = {
        "companies.xlsx": 1,
        "profitandloss.xlsx": 1,
        "balancesheet.xlsx": 1,
        "cashflow.xlsx": 1,
        "analysis.xlsx": 1,
        "documents.xlsx": 1,
        "prosandcons.xlsx": 1,
        "financial_ratios.xlsx": 0,
        "market_cap.xlsx": 0,
        "peer_groups.xlsx": 0,
        "sectors.xlsx": 0,
        "stock_prices.xlsx": 0,
    }

    loaded_data = {}

    for filename, header in datasets.items():

        file = RAW_DATA / filename

        df = load_excel(file, header)

        if df is not None:
            loaded_data[filename] = df

    return loaded_data


if __name__ == "__main__":

    data = load_all_files()

    print("\nSummary")

    for name, df in data.items():
        print(f"{name} --> {df.shape}")