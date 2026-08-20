from __future__ import annotations
import pandas as pd


ALERT_COLUMNS = [
    "TransactionKey", "FraudScore", "RiskLevel", "AlertLevel", "AlertStatus",
    "RecommendedAction", "ModelVersion", "PolicyVersion", "ScoredAt",
]


def generate_alerts(scored: pd.DataFrame, existing: pd.DataFrame | None = None) -> pd.DataFrame:
    """Create HIGH/CRITICAL alerts and remove existing transaction/model pairs."""
    required = set(ALERT_COLUMNS) | {"CreateAlert"}
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"Missing alert columns: {missing}")
    alerts = scored.loc[scored["CreateAlert"], ALERT_COLUMNS].copy()
    alerts = alerts.drop_duplicates(["TransactionKey", "ModelVersion"], keep="first")
    if existing is not None and not existing.empty:
        old_keys = pd.MultiIndex.from_frame(existing[["TransactionKey", "ModelVersion"]])
        new_keys = pd.MultiIndex.from_frame(alerts[["TransactionKey", "ModelVersion"]])
        alerts = alerts.loc[~new_keys.isin(old_keys)]
    return alerts.reset_index(drop=True)
