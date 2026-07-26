import streamlit as st
import sys
from pathlib import Path

# Add project root to path so we can import utils safely
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Standard configuration
st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("Nifty 100 Analytics - Dashboard")
    st.write("Welcome to the Nifty 100 Financial Intelligence Platform.")
    st.write("Please use the sidebar to navigate through the dashboard screens.")
    
    st.info("👈 Select a module from the sidebar to begin.")

if __name__ == "__main__":
    main()
