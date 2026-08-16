from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, fbeta_score, precision_score, recall_score


def evaluate_scores(y_true, scores, threshold: float, amounts=None) -> dict:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    pred = (s >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    result = {
        "pr_auc": float(average_precision_score(y, s)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f2": float(fbeta_score(y, pred, beta=2, zero_division=0)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        "alert_count": int(pred.sum()),
        "alerts_per_1000": float(pred.mean() * 1000),
    }
    if amounts is not None:
        amount = np.asarray(amounts, dtype=float)
        fraud_mask = y == 1
        captured = float(amount[fraud_mask & (pred == 1)].sum())
        missed = float(amount[fraud_mask & (pred == 0)].sum())
        total = captured + missed
        result.update({
            "fraud_amount_captured": captured,
            "fraud_amount_missed": missed,
            "fraud_amount_capture_rate": float(captured / total) if total else 0.0,
        })
    return result
