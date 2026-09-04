from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_repo = Path(__file__).resolve().parents[3]
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from src.common.database import get_connection
from dashboard.streamlit.components.filters import load_sidebar_filters, fmt_amount, fmt_pct


def db_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()


st.title("Operations")
st.caption("ETL pipeline health and data quality monitoring")

filters = load_sidebar_filters()

# ETL Quality Summary
st.subheader("ETL Quality Summary (KPI-Q01 / KPI-Q02)")
etl_sql = """
    SELECT
        BatchID, SourceFileName, BatchStatus,
        SourceRows, FactRows, ReconStatus,
        ReconciliationRate, RejectCount, ValidationErrorRate
    FROM bi.vw_ETLQualitySummary
    ORDER BY BatchID DESC
"""
etl_df = db_query(etl_sql)

if etl_df.empty:
    st.info("No ETL batch records found.")
else:
    latest = etl_df.iloc[0]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Latest Batch", f"#{int(latest['BatchID'])}")
    k2.metric("Reconciliation Rate", fmt_pct(float(latest["ReconciliationRate"])))
    k3.metric("Validation Error Rate", fmt_pct(float(latest["ValidationErrorRate"])))
    k4.metric("Batch Status", str(latest["BatchStatus"]))

    st.divider()
    st.dataframe(
        etl_df,
        column_config={
            "BatchID": st.column_config.NumberColumn("Batch ID"),
            "SourceFileName": st.column_config.TextColumn("Source File"),
            "BatchStatus": st.column_config.TextColumn("Status"),
            "SourceRows": st.column_config.NumberColumn("Source Rows"),
            "FactRows": st.column_config.NumberColumn("Fact Rows"),
            "ReconStatus": st.column_config.TextColumn("Recon Status"),
            "ReconciliationRate": st.column_config.NumberColumn("Recon Rate", format="%.4f"),
            "RejectCount": st.column_config.NumberColumn("Rejects"),
            "ValidationErrorRate": st.column_config.NumberColumn("Error Rate", format="%.6f"),
        },
        use_container_width=True,
        hide_index=True,
    )

# Reject log drill-down
st.divider()
st.subheader("Reject Log")
reject_sql = """
    SELECT BatchID, ChunkIndex, StepRaw, Reason, CreatedAt
    FROM audit.RejectLog
    ORDER BY RejectID DESC
"""
reject_df = db_query(reject_sql)
if reject_df.empty:
    st.success("No rejected rows. ETL validation passed cleanly.")
else:
    st.dataframe(reject_df, use_container_width=True, hide_index=True)

    # Reason distribution
    reason_counts = reject_df["Reason"].value_counts().reset_index()
    reason_counts.columns = ["Reason", "Count"]
    st.bar_chart(reason_counts.set_index("Reason"))

# Batch log
st.divider()
st.subheader("ETL Batch Log")
batch_sql = """
    SELECT BatchID, SourceFileName, Status, StartedAt, FinishedAt, Message
    FROM audit.ETLBatchLog
    ORDER BY BatchID DESC
"""
batch_df = db_query(batch_sql)
if not batch_df.empty:
    st.dataframe(batch_df, use_container_width=True, hide_index=True)
