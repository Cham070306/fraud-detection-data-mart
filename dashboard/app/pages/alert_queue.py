from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

_repo = Path(__file__).resolve().parents[3]
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from src.common.database import execute, get_connection


def db_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)
    finally:
        conn.close()


st.title("Alert Queue")
st.caption("Review and act on HIGH / CRITICAL fraud alerts")

# Summary strip
summary_sql = """
    SELECT
        COUNT_BIG(*) AS total,
        SUM(CASE WHEN AnalystDecision = 'CONFIRMED_FRAUD' THEN 1 ELSE 0 END) AS confirmed,
        SUM(CASE WHEN AnalystDecision = 'FALSE_POSITIVE' THEN 1 ELSE 0 END) AS false_pos,
        SUM(CASE WHEN AnalystDecision = 'UNDER_INVESTIGATION' THEN 1 ELSE 0 END) AS under_inv,
        SUM(CASE WHEN AnalystDecision IS NULL THEN 1 ELSE 0 END) AS open_count
    FROM bi.vw_AlertQueue
"""
s = db_query(summary_sql).iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Alerts", f"{int(s['total']):,}")
c2.metric("Confirmed Fraud", f"{int(s['confirmed']):,}")
c3.metric("False Positive", f"{int(s['false_pos']):,}")
c4.metric("Under Investigation", f"{int(s['under_inv']):,}")
c5.metric("Open", f"{int(s['open_count']):,}")

st.divider()

# Filters
col_f1, col_f2 = st.columns(2)
with col_f1:
    risk_filter = st.multiselect(
        "Risk Level", ["HIGH", "CRITICAL"], default=["HIGH", "CRITICAL"]
    )
with col_f2:
    decision_filter = st.multiselect(
        "Decision",
        ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "UNDER_INVESTIGATION"],
        default=[],
    )

# Build query
risk_list = ",".join(f"'{r}'" for r in risk_filter)
where_parts = [f"RiskLevel IN ({risk_list})"]
if decision_filter:
    dec_list = ",".join(f"'{d}'" for d in decision_filter)
    where_parts.append(f"ISNULL(AnalystDecision, 'OPEN') IN ({dec_list})")
where = " AND ".join(where_parts)

alerts_sql = f"""
    SELECT AlertKey, TransactionKey, StepDay, TypeCode, Amount,
           FraudScore, RiskLevel, AlertLevel, AlertStatus,
           RecommendedAction, AnalystDecision, FeedbackComment,
           ReviewedBy, ReviewedAt
    FROM bi.vw_AlertQueue
    WHERE {where}
    ORDER BY
        CASE AlertLevel WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 END,
        FraudScore DESC
"""
alerts = db_query(alerts_sql)

if alerts.empty:
    st.info("No alerts match the current filters.")
else:
    st.dataframe(
        alerts,
        column_config={
            "AlertKey": st.column_config.NumberColumn("Alert Key"),
            "TransactionKey": st.column_config.NumberColumn("Transaction"),
            "Amount": st.column_config.NumberColumn("Amount", format="%.2f"),
            "FraudScore": st.column_config.NumberColumn("Score", format="%.6f"),
            "RiskLevel": st.column_config.TextColumn("Risk"),
            "AlertLevel": st.column_config.TextColumn("Level"),
            "AlertStatus": st.column_config.TextColumn("Status"),
            "AnalystDecision": st.column_config.TextColumn("Decision"),
            "ReviewedBy": st.column_config.TextColumn("Reviewed By"),
            "ReviewedAt": st.column_config.TextColumn("Reviewed At"),
        },
        use_container_width=True,
        hide_index=True,
    )

# Feedback form
st.divider()
st.subheader("Submit Analyst Feedback")

if not alerts.empty:
    alert_options = {
        f"#{int(r['AlertKey'])} | Txn {int(r['TransactionKey'])} | {r['RiskLevel']} | Score {r['FraudScore']:.4f}": int(r["AlertKey"])
        for _, r in alerts.iterrows()
    }
    selected_label = st.selectbox("Select Alert", list(alert_options.keys()))
    selected_key = alert_options[selected_label]

    with st.form("feedback_form"):
        decision = st.radio(
            "Decision",
            ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "UNDER_INVESTIGATION"],
            horizontal=True,
        )
        comment = st.text_area("Comment (optional)", max_chars=500)
        reviewer = st.text_input("Analyst Name", max_chars=100)
        submitted = st.form_submit_button("Submit Feedback", type="primary")

        if submitted:
            if not reviewer.strip():
                st.error("Please enter analyst name.")
            else:
                status_map = {
                    "CONFIRMED_FRAUD": "RESOLVED",
                    "FALSE_POSITIVE": "FALSE_POSITIVE",
                    "UNDER_INVESTIGATION": "IN_REVIEW",
                }
                try:
                    execute(
                        get_connection(),
                        """
                        UPDATE fact.FactAlert
                        SET AnalystDecision = ?,
                            AlertStatus = ?,
                            FeedbackComment = ?,
                            ReviewedBy = ?,
                            ReviewedAt = SYSDATETIME()
                        WHERE AlertKey = ?
                        """,
                        (decision, status_map[decision], comment or None, reviewer.strip(), selected_key),
                    )
                    st.success(f"Feedback submitted for Alert #{selected_key}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")
else:
    st.info("No alerts available for feedback.")
