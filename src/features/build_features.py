"""Leakage-safe feature engineering for PaySim transactions."""
from __future__ import annotations

import numpy as np
import pandas as pd

TARGET_COLUMN = "isFraud"
EXCLUDED_COLUMNS = {
    TARGET_COLUMN, "isFlaggedFraud", "FraudScore", "RiskLevel", "AlertStatus",
    "PredictedFraud", "TransactionKey", "nameOrig", "nameDest",
}


def _safe_ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    result = num.astype(float).div(den.astype(float).replace(0, np.nan))
    return result.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic, point-in-time features without the target."""
    required = {
        "step", "type", "amount", "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    x = pd.DataFrame(index=frame.index)
    x["TransactionType"] = frame["type"].astype(object).fillna("UNKNOWN").astype(str)
    amount = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0).clip(lower=0)
    old_orig = pd.to_numeric(frame["oldbalanceOrg"], errors="coerce").fillna(0.0)
    new_orig = pd.to_numeric(frame["newbalanceOrig"], errors="coerce").fillna(0.0)
    old_dest = pd.to_numeric(frame["oldbalanceDest"], errors="coerce").fillna(0.0)
    new_dest = pd.to_numeric(frame["newbalanceDest"], errors="coerce").fillna(0.0)
    step = pd.to_numeric(frame["step"], errors="coerce").fillna(0).astype(int)

    x["Amount"] = amount
    x["LogAmount"] = np.log1p(amount)
    x["StepRaw"] = step
    x["Hour"] = step.mod(24)
    x["Day"] = step.floordiv(24) + 1
    x["OldBalanceOrig"] = old_orig
    x["NewBalanceOrig"] = new_orig
    x["BalanceChangeOrig"] = new_orig - old_orig
    x["BalanceDropOrig"] = (old_orig - new_orig).clip(lower=0)
    x["OrigBalanceError"] = old_orig - amount - new_orig
    x["OldBalanceDest"] = old_dest
    x["NewBalanceDest"] = new_dest
    x["BalanceChangeDest"] = new_dest - old_dest
    x["DestBalanceError"] = old_dest + amount - new_dest
    x["AmountToOrigBalance"] = _safe_ratio(amount, old_orig)
    x["AmountToDestBalance"] = _safe_ratio(amount, old_dest)
    x["OrigBalanceBecomesZero"] = ((old_orig > 0) & (new_orig == 0)).astype(int)
    x["DestBalanceWasZero"] = (old_dest == 0).astype(int)
    x["IsTransfer"] = frame["type"].eq("TRANSFER").astype(int)
    x["IsCashOut"] = frame["type"].eq("CASH_OUT").astype(int)
    return x.replace([np.inf, -np.inf], 0).fillna(0)


def feature_columns() -> list[str]:
    sample = pd.DataFrame({
        "step": [1], "type": ["PAYMENT"], "amount": [1.0],
        "oldbalanceOrg": [1.0], "newbalanceOrig": [0.0],
        "oldbalanceDest": [0.0], "newbalanceDest": [1.0],
    })
    return build_features(sample).columns.tolist()
