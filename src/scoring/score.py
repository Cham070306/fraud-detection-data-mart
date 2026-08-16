from __future__ import annotations

from datetime import datetime, timezone
import joblib
import pandas as pd

from src.features.build_features import build_features
from .alert_engine import classify_risk, load_policy


def score_transactions(frame, model_path, metadata, policy_path):
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
    out["TransactionKey"] = frame["TransactionKey"] if "TransactionKey" in frame else frame.index.astype(str)
    step = pd.to_numeric(frame["step"], errors="coerce").fillna(0).astype(int)
    out["DateKey"] = step.floordiv(24) + 1
    out["TimeKey"] = step.mod(24)
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
