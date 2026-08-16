from __future__ import annotations

import numpy as np
import pandas as pd
from .evaluate import evaluate_scores


def threshold_table(y_true, scores, thresholds=None, amounts=None) -> pd.DataFrame:
    thresholds = np.asarray(thresholds if thresholds is not None else np.linspace(0.05, 0.95, 91))
    return pd.DataFrame([{"threshold": float(t), **evaluate_scores(y_true, scores, float(t), amounts)} for t in thresholds])


def select_threshold(y_true, scores, *, min_recall: float = 0.80, max_alerts_per_1000: float | None = None, amounts=None):
    table = threshold_table(y_true, scores, amounts=amounts)
    eligible = table[table["recall"] >= min_recall]
    if max_alerts_per_1000 is not None:
        eligible = eligible[eligible["alerts_per_1000"] <= max_alerts_per_1000]
    chosen = (eligible if not eligible.empty else table).sort_values(["f2", "precision", "threshold"], ascending=False).iloc[0]
    return float(chosen["threshold"]), table
