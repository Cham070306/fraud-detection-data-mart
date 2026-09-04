from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass

import pandas as pd
import streamlit as st

_repo = Path(__file__).resolve().parents[3]
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from src.common.database import get_connection


@dataclass
class Filters:
    step_day_min: int
    step_day_max: int
    type_codes: list[str]
    risk_levels: list[str]
    model_version: str | None


def db_query(sql: str, params: tuple = ()) -> pd.DataFrame:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=columns)
    finally:
        conn.close()


def fmt_amount(value: float) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"
    if value >= 1_000:
        return f"{value / 1_000:,.2f}K"
    return f"{value:,.2f}"


def fmt_pct(value: float) -> str:
    return f"{value * 100:.4f}%"


def load_sidebar_filters() -> Filters:
    with st.sidebar:
        st.divider()
        st.markdown("### Filters")

        day_range = db_query("SELECT MIN(StepDay) AS mn, MAX(StepDay) AS mx FROM dim.DimDate")
        day_min, day_max = int(day_range["mn"].iloc[0]), int(day_range["mx"].iloc[0])
        step_days = st.slider("Step Day Range", day_min, day_max, (day_min, day_max))

        types_df = db_query("SELECT TypeCode FROM dim.DimTransactionType ORDER BY TypeCode")
        all_types = types_df["TypeCode"].tolist()
        selected_types = st.multiselect("Transaction Type", all_types, default=all_types)

        risk_df = db_query("SELECT DISTINCT RiskLevel FROM dim.DimRiskPolicy ORDER BY RiskLevel")
        all_risks = risk_df["RiskLevel"].tolist()
        selected_risks = st.multiselect("Risk Level", all_risks, default=all_risks)

        ver_df = db_query("SELECT Version FROM dim.DimModelVersion WHERE IsProduction = 1")
        versions = ver_df["Version"].tolist() if not ver_df.empty else ["1.0.0"]
        selected_ver = st.selectbox("Model Version", versions)

    return Filters(
        step_day_min=step_days[0],
        step_day_max=step_days[1],
        type_codes=selected_types,
        risk_levels=selected_risks,
        model_version=selected_ver,
    )
