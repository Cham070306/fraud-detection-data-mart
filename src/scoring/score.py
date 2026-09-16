from __future__ import annotations

from datetime import datetime, timezone
import joblib
import pandas as pd

from src.features.build_features import build_features
from src.common.config import DEFAULT_START_DATE
from src.common.time_mapping import derive_simulation_time
from .alert_engine import classify_risk, load_policy


def score_transactions(
    frame, model_path, metadata, policy_path, start_date: str = DEFAULT_START_DATE
):
    model = joblib.load(model_path)
    x = build_features(frame)
    expected = list(metadata["feature_list"])
    missing = sorted(set(expected) - set(x.columns))
    if missing:
        raise ValueError(f"Missing model features: {missing}")
    scores = model.predict_proba(x[expected])[:, 1]
    policy = load_policy(policy_path)
    rows = [classify_risk(float(s), policy) for s in scores]
    out = pd.DataFrame(index=frame.index)
    if "TransactionKey" not in frame:
        raise ValueError(
            "TransactionKey is required for production scoring. "
            "Use --from-sql or provide an input that was exported from FactTransaction."
        )
    out["TransactionKey"] = pd.to_numeric(frame["TransactionKey"], errors="raise").astype("int64")
    if "DateKey" in frame and "TimeKey" in frame:
        out["DateKey"] = pd.to_numeric(frame["DateKey"], errors="raise").astype(int)
        out["TimeKey"] = pd.to_numeric(frame["TimeKey"], errors="raise").astype(int)
    else:
        time_keys = derive_simulation_time(frame["step"], start_date)
        out["DateKey"] = time_keys["DateKey"]
        out["TimeKey"] = time_keys["TimeKey"]
    out["TransactionType"] = frame["type"].astype(object).fillna("UNKNOWN").astype(str)
    out["Amount"] = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0)
    out["FraudScore"] = scores
    out["PredictedFraud"] = (scores >= float(metadata["threshold"])).astype(int)
    out[["RiskLevel", "CreateAlert", "RecommendedAction"]] = rows
    out["AlertLevel"] = out["RiskLevel"].where(out["CreateAlert"], "NONE")
    out["AlertStatus"] = out["CreateAlert"].map({True: "NEW", False: "NONE"})
    out["ModelVersion"] = metadata["version"]
    out["PolicyVersion"] = policy["policy_version"]
    out["ScoredAt"] = datetime.now(timezone.utc).isoformat()
    return out
