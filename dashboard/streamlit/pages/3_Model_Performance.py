from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

_repo = Path(__file__).resolve().parents[3]
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from src.common.database import get_connection
from dashboard.streamlit.components.filters import load_sidebar_filters, fmt_pct


def db_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()


st.title("Model Performance")
st.caption("ML model evaluation metrics (TEST split only)")

filters = load_sidebar_filters()

# Load model metadata
meta_path = _repo / "models" / "fraud_model_v1.0.0_metadata.json"
if meta_path.exists():
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    test_metrics = meta.get("test_metrics", meta.get("validation_metrics", {}))
    val_metrics = meta.get("validation_metrics", {})
else:
    test_metrics = {}
    val_metrics = {}

# KPI cards
st.subheader("Test Set Metrics (v1.0.0)")
kpi_cols = st.columns(5)
kpi_data = [
    ("Precision", test_metrics.get("precision", val_metrics.get("precision", 0))),
    ("Recall", test_metrics.get("recall", val_metrics.get("recall", 0))),
    ("F2-Score", test_metrics.get("f2", val_metrics.get("f2", 0))),
    ("PR-AUC", test_metrics.get("pr_auc", val_metrics.get("pr_auc", 0))),
    ("Threshold", meta.get("threshold", 0.32)),
]
for col, (label, value) in zip(kpi_cols, kpi_data):
    col.metric(label, f"{value:.6f}" if isinstance(value, float) else str(value))

# Capture rate
if "fraud_amount_capture_rate" in test_metrics:
    st.metric("Fraud Amount Capture Rate", fmt_pct(test_metrics["fraud_amount_capture_rate"]))

st.divider()

# Confusion matrix
st.subheader("Confusion Matrix")
cm = {
    "tn": test_metrics.get("tn", val_metrics.get("tn", 0)),
    "fp": test_metrics.get("fp", val_metrics.get("fp", 0)),
    "fn": test_metrics.get("fn", val_metrics.get("fn", 0)),
    "tp": test_metrics.get("tp", val_metrics.get("tp", 0)),
}
cm_cols = st.columns(4)
cm_cols[0].metric("True Negative", f"{cm['tn']:,}")
cm_cols[1].metric("False Positive", f"{cm['fp']:,}")
cm_cols[2].metric("False Negative", f"{cm['fn']:,}")
cm_cols[3].metric("True Positive", f"{cm['tp']:,}")

# Risk level legend
st.divider()
st.subheader("Risk Policy (v1.0.0)")
policy = st.session_state.get("risk_policy", {})
levels = policy.get("risk_levels", [])
if levels:
    legend_df = pd.DataFrame([
        {
            "Risk Level": lv.get("level", "").upper(),
            "Score Range": f"[{lv.get('min_score', 0):.2f}, {lv.get('max_score', 1):.2f})",
            "Alert": "Yes" if lv.get("alert") else "No",
            "Action": lv.get("action", ""),
        }
        for lv in levels
    ])
    st.dataframe(legend_df, use_container_width=True, hide_index=True)

# Model version selector
st.divider()
st.subheader("Model Registry")
reg_path = _repo / "models" / "registry.json"
if reg_path.exists():
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    active = registry.get("active_version", "unknown")
    st.write(f"**Active Version:** {active}")
    models = registry.get("models", {})
    if models:
        reg_df = pd.DataFrame([
            {
                "Version": v,
                "Model Name": m.get("model_name", ""),
                "Threshold": m.get("threshold", ""),
                "Status": m.get("status", ""),
                "Created At": m.get("created_at", ""),
            }
            for v, m in models.items()
        ])
        st.dataframe(reg_df, use_container_width=True, hide_index=True)
