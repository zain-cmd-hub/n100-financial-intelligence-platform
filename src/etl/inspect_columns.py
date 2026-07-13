from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA = BASE_DIR / "data" / "raw"

files = [
    "financial_ratios.xlsx",
    "market_cap.xlsx",
    "peer_groups.xlsx",
    "sectors.xlsx",
    "stock_prices.xlsx"
]

for filename in files:

    file_path = RAW_DATA / filename

    print("\n" + "=" * 70)
    print(f"FILE: {filename}")

    # Read without assuming any header
    df = pd.read_excel(
        file_path,
        header=None
    )

    print(df.head(5).to_string())