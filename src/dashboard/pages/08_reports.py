import sys
from pathlib import Path

import requests
import streamlit as st

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from src.dashboard.utils.db import get_companies, get_documents

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports Archive")

companies = get_companies()
if companies.empty:
    st.error("No companies data available.")
    st.stop()

# Prepare search box data
companies["search_key"] = companies["id"] + " - " + companies["company_name"]
search_keys = companies["search_key"].tolist()

selected_key = st.selectbox(
    "Search by Ticker or Company Name", options=[""] + search_keys, index=0
)

if not selected_key:
    st.info("Please select a company to view its annual reports.")
    st.stop()

ticker = selected_key.split(" - ")[0]
st.subheader(f"Available Annual Reports: {ticker}")
st.markdown("---")

docs = get_documents(ticker)

if docs.empty:
    st.warning("No annual reports found in the database for this company.")
    st.stop()

# Sort by year descending
docs = docs.sort_values(by="year", ascending=False)


def check_url(url):
    """Handles operations for check_url."""
    try:
        # Use a short timeout to prevent UI blocking.
        # Some servers block HEAD requests, so we use a GET request with stream=True
        r = requests.get(url, stream=True, timeout=3)
        return r.status_code != 404
    except Exception:
        return False


# Display reports nicely
for _, row in docs.iterrows():
    year = row["year"]
    url = row["annual_report"]

    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"### **FY {year}**")

    with col2:
        # Verify URL live
        is_valid = check_url(url)

        if is_valid:
            st.markdown(f"✅ [Download BSE PDF Report]({url})")
        else:
            st.markdown(
                f"🔴 <span style='color:red; font-weight:bold;'>[Report Unavailable (404)]</span> - Link broken: {url}",
                unsafe_allow_html=True,
            )

    st.markdown("---")
