from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.features.build_features import TARGET_COLUMN, build_features
from .evaluate import evaluate_scores
from .threshold import select_threshold


class BusinessRuleClassifier(ClassifierMixin, BaseEstimator):
    """Transparent PaySim baseline using only point-in-time transaction features."""
    def fit(self, x, y=None):
        self.classes_ = np.array([0, 1]); self.n_features_in_ = x.shape[1]
        self.feature_names_in_ = np.asarray(x.columns, dtype=object)
        return self

    def predict_proba(self, x):
        risky_type = x["TransactionType"].isin(["TRANSFER", "CASH_OUT"]).to_numpy()
        drained = x["OrigBalanceBecomesZero"].astype(bool).to_numpy()
        large = (x["Amount"] >= 200_000).to_numpy()
        balance_error = (x["OrigBalanceError"].abs() >= 1.0).to_numpy()
        score = np.where(risky_type & drained & (large | balance_error), .90,
                np.where(risky_type & drained, .65, np.where(risky_type & large, .35, .05)))
        return np.column_stack([1.0-score, score])


def temporal_split(frame: pd.DataFrame, train_fraction=.70, validation_fraction=.15):
    ordered = frame.sort_values("step", kind="stable")
    unique_steps = np.sort(ordered["step"].unique())
    if len(unique_steps) < 3:
        raise ValueError("At least 3 distinct step values are required for temporal split")
    train_cut = unique_steps[max(0, min(len(unique_steps)-3, int(len(unique_steps)*train_fraction)-1))]
    val_idx = max(1, min(len(unique_steps)-2, int(len(unique_steps)*(train_fraction+validation_fraction))-1))
    val_cut = unique_steps[val_idx]
    return ordered[ordered.step <= train_cut], ordered[(ordered.step > train_cut) & (ordered.step <= val_cut)], ordered[ordered.step > val_cut]


def _pipeline(model):
    categorical = ["TransactionType"]
    numeric = [c for c in build_features(pd.DataFrame({"step":[1],"type":["PAYMENT"],"amount":[1],"oldbalanceOrg":[1],"newbalanceOrig":[0],"oldbalanceDest":[0],"newbalanceDest":[1]})).columns if c not in categorical]
    prep = ColumnTransformer([
        ("num", Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]), numeric),
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ])
    return Pipeline([("preprocess", prep), ("model", model)])


def _stratified_cap(x, y, max_rows: int, random_state: int):
    """Keep every fraud row and sample non-fraud rows for scalable tree fitting."""
    if len(x) <= max_rows:
        return x, y
    positives = y[y == 1].index
    negative_budget = max(max_rows - len(positives), len(positives))
    negatives = y[y == 0].sample(n=min(negative_budget, int((y == 0).sum())), random_state=random_state).index
    selected = positives.union(negatives).sort_values()
    return x.loc[selected], y.loc[selected]


def train_models(frame: pd.DataFrame, random_state=42, rf_max_train_rows=500_000):
    if TARGET_COLUMN not in frame:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")
    train, validation, test = temporal_split(frame)
    datasets = [(build_features(d), d[TARGET_COLUMN].astype(int)) for d in (train, validation, test)]
    x_train, y_train = datasets[0]
    x_val, y_val = datasets[1]
    models = {
        "baseline_rule": BusinessRuleClassifier(),
        "logistic_regression": _pipeline(LogisticRegression(class_weight="balanced", max_iter=1000, random_state=random_state)),
        "random_forest": _pipeline(RandomForestClassifier(n_estimators=120, max_depth=16, min_samples_leaf=2, class_weight="balanced_subsample", n_jobs=-1, random_state=random_state)),
    }
    results = {}
    for name, pipeline in models.items():
        fit_x, fit_y = (x_train, y_train)
        if name == "random_forest":
            fit_x, fit_y = _stratified_cap(x_train, y_train, rf_max_train_rows, random_state)
        pipeline.fit(fit_x, fit_y)
        val_scores = pipeline.predict_proba(x_val)[:, 1]
        threshold, _ = select_threshold(y_val, val_scores, min_recall=0.80, amounts=validation["amount"])
        results[name] = {
            "pipeline": pipeline, "threshold": threshold,
            "training_rows": int(len(fit_x)),
            "validation": evaluate_scores(y_val, val_scores, threshold, validation["amount"]),
            "data_split": {
                "train": {"step_min": int(train.step.min()), "step_max": int(train.step.max()), "rows": int(len(train)), "fraud_rows": int(y_train.sum())},
                "validation": {"step_min": int(validation.step.min()), "step_max": int(validation.step.max()), "rows": int(len(validation)), "fraud_rows": int(y_val.sum())},
                "test": {"step_min": int(test.step.min()), "step_max": int(test.step.max()), "rows": int(len(test)), "fraud_rows": int(datasets[2][1].sum())},
            },
            "sampling_strategy": "all rows" if name != "random_forest" or len(fit_x) == len(x_train) else "all fraud rows plus deterministic non-fraud sample",
        }
    selected_name = max(results, key=lambda n: results[n]["validation"]["f2"])
    selected = results[selected_name]
    x_test, y_test = datasets[2]
    test_scores = selected["pipeline"].predict_proba(x_test)[:, 1]
    selected["test"] = evaluate_scores(y_test, test_scores, selected["threshold"], test["amount"])
    return selected_name, results


def save_model(selected_name, result, output_dir, version="1.0.0", training_data_source=None, policy_version="1.0.0", git_commit=None):
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    artifact = out / f"fraud_model_v{version}.joblib"
    joblib.dump(result["pipeline"], artifact)
    metadata = {
        "model_name": selected_name, "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "threshold": result["threshold"], "validation_metrics": result["validation"],
        "test_metrics": result.get("test", {}),
        "training_rows": result.get("training_rows"),
        "training_data_source": training_data_source,
        "data_split": result.get("data_split"),
        "sampling_strategy": result.get("sampling_strategy"),
        "risk_policy_version": policy_version,
        "git_commit": git_commit,
        "algorithm_parameters": result["pipeline"].named_steps["model"].get_params() if hasattr(result["pipeline"], "named_steps") else result["pipeline"].get_params(),
        "feature_list": list(result["pipeline"].feature_names_in_),
    }
    artifact.with_name(f"fraud_model_v{version}_metadata.json").write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
    artifact.with_name(f"fraud_model_v{version}_features.json").write_text(json.dumps(metadata["feature_list"], indent=2), encoding="utf-8")
    return artifact, metadata
