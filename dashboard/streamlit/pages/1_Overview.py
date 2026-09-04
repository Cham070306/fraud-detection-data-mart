from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
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


st.title("Overview")
st.caption("Transaction KPIs and fraud distribution")

filters = load_sidebar_filters()

type_list = ",".join(f"'{t}'" for t in filters.type_codes)
risk_list = ",".join(f"'{r}'" for r in filters.risk_levels)

# KPI cards
kpi_sql = f"""
SELECT
    ISNULL(SUM(TransactionCount), 0) AS volume,
    ISNULL(SUM(TotalAmount), 0) AS amount,
    ISNULL(SUM(FraudCount), 0) AS fraud_count,
    ISNULL(SUM(FraudCount * TotalAmount / NULLIF(TransactionCount, 0)), 0) AS fraud_amount
FROM bi.vw_TransactionSummary
WHERE StepDay BETWEEN {filters.step_day_min} AND {filters.step_day_max}
  AND TypeCode IN ({type_list})
"""
kpi = db_query(kpi_sql).iloc[0]
vol = int(kpi["volume"])
amt = float(kpi["amount"])
f_vol = int(kpi["fraud_count"])
f_amt = float(kpi["fraud_amount"])

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Volume", f"{vol:,}")
c2.metric("Amount", fmt_amount(amt))
c3.metric("Fraud Count", f"{f_vol:,}")
c4.metric("Fraud Amount", fmt_amount(f_amt))
c5.metric("Fraud Rate (Vol)", fmt_pct(f_vol / vol if vol else 0.0))
c6.metric("Fraud Rate (Amt)", fmt_pct(f_amt / amt if amt else 0.0))

st.divider()

# Charts
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Fraud by Transaction Type")
    df_type = db_query(f"""
        SELECT TypeCode, SUM(TransactionCount) AS volume, SUM(FraudCount) AS fraud_count
        FROM bi.vw_TransactionSummary
        WHERE StepDay BETWEEN {filters.step_day_min} AND {filters.step_day_max}
          AND TypeCode IN ({type_list})
        GROUP BY TypeCode ORDER BY volume DESC
    """)
    if not df_type.empty:
        fig = px.bar(df_type, x="TypeCode", y="fraud_count", color="TypeCode",
                     labels={"TypeCode": "Type", "fraud_count": "Fraud Count"})
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Fraud by Amount Band")
    df_band = db_query("""
        SELECT ab.BandCode, ab.BandLabel,
               COUNT_BIG(*) AS volume,
               SUM(CASE WHEN ft.IsFraud = 1 THEN 1 ELSE 0 END) AS fraud_count
        FROM fact.FactTransaction ft
        JOIN dim.DimAmountBand ab ON ft.AmountBandKey = ab.AmountBandKey
        WHERE ft.StepRaw BETWEEN ? AND ?
        GROUP BY ab.BandCode, ab.BandLabel
        ORDER BY ab.AmountBandKey
    """, (filters.step_day_min, filters.step_day_max))
    if not df_band.empty:
        fig = px.bar(df_band, x="BandLabel", y="fraud_count", color="BandCode",
                     labels={"BandLabel": "Amount Band", "fraud_count": "Fraud Count"})
        st.plotly_chart(fig, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Fraud Volume by Day")
    df_day = db_query(f"""
        SELECT StepDay, SUM(TransactionCount) AS volume, SUM(FraudCount) AS fraud_count
        FROM bi.vw_TransactionSummary
        WHERE StepDay BETWEEN {filters.step_day_min} AND {filters.step_day_max}
          AND TypeCode IN ({type_list})
        GROUP BY StepDay ORDER BY StepDay
    """)
    if not df_day.empty:
        fig = px.line(df_day, x="StepDay", y="fraud_count", markers=True,
                      labels={"StepDay": "Day", "fraud_count": "Fraud Count"})
        st.plotly_chart(fig, use_container_width=True)

with col_d:
    st.subheader("Fraud by Time Slot")
    df_slot = db_query("""
        SELECT t.TimeSlot,
               COUNT_BIG(*) AS volume,
               SUM(CASE WHEN ft.IsFraud = 1 THEN 1 ELSE 0 END) AS fraud_count
        FROM fact.FactTransaction ft
        JOIN dim.DimTime t ON ft.TimeKey = t.TimeKey
        WHERE ft.StepRaw BETWEEN ? AND ?
        GROUP BY t.TimeSlot
        ORDER BY fraud_count DESC
    """, (filters.step_day_min, filters.step_day_max))
    if not df_slot.empty:
        fig = px.bar(df_slot, x="TimeSlot", y="fraud_count", color="TimeSlot",
                     labels={"TimeSlot": "Time Slot", "fraud_count": "Fraud Count"})
        st.plotly_chart(fig, use_container_width=True)
