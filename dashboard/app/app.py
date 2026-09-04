from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

_repo = Path(__file__).resolve().parents[1]
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.markdown("## :shield: Fraud Detection Dashboard")
st.sidebar.caption("PaySim Fraud Detection Data Mart")

try:
    from src.common.database import get_connection
    conn = get_connection()
    conn.close()
    st.sidebar.success("DB Connected", icon=":white_check_mark:")
except Exception:
    st.sidebar.error("DB Offline", icon=":x:")

st.sidebar.divider()
st.sidebar.markdown(
    "**Pages**\n"
    "- **Alert Queue** — Review and act on fraud alerts\n"
    "- Use the sidebar navigation to switch pages"
)

st.title("PaySim Fraud Detection Data Mart")
st.markdown(
    "Executive dashboard for transaction fraud monitoring, ML model performance, "
    "analyst feedback workflow, and ETL quality tracking."
)

col1, col2 = st.columns(2)
with col1:
    st.info(
        "**Quick Start**\n"
        "- Navigate to **Alert Queue** to review and act on fraud alerts\n"
        "- Use the sidebar to switch between pages"
    )
with col2:
    st.info(
        "**Data Notes**\n"
        "- PaySim synthetic dataset (simulated transactions)\n"
        "- `step` is simulated time (not real calendar dates)\n"
        "- Model: Random Forest v1.0.0, threshold 0.32"
    )
