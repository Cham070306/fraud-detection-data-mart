import json
import numpy as np
import pandas as pd

from src.features.build_features import build_features
from src.training.train import save_model, train_models
from src.training.evaluate import evaluate_scores
from src.scoring.score import score_transactions


def sample_frame(n=180):
    rng = np.random.default_rng(7)
    step = np.repeat(np.arange(1, 19), n // 18)
    amount = rng.lognormal(8, 1.2, len(step))
    tx_type = rng.choice(["PAYMENT", "TRANSFER", "CASH_OUT"], len(step))
    fraud = ((tx_type == "TRANSFER") & (amount > np.quantile(amount, .82))).astype(int)
    old_orig = amount * rng.uniform(.5, 2.0, len(step))
    return pd.DataFrame({
        "step": step, "type": tx_type, "amount": amount,
        "nameOrig": [f"C{i}" for i in range(len(step))],
        "oldbalanceOrg": old_orig, "newbalanceOrig": np.maximum(old_orig-amount, 0),
        "nameDest": [f"D{i}" for i in range(len(step))],
        "oldbalanceDest": rng.uniform(0, 10000, len(step)),
        "newbalanceDest": rng.uniform(0, 10000, len(step)) + amount,
        "isFraud": fraud, "isFlaggedFraud": 0,
        "TransactionKey": np.arange(1000, 1000+len(step)),
    })


def test_features_have_no_leakage_or_invalid_values():
    x = build_features(sample_frame())
    assert not {"isFraud", "isFlaggedFraud", "TransactionKey"} & set(x.columns)
    assert np.isfinite(x.select_dtypes(include="number").to_numpy()).all()


def test_train_save_load_and_score_preserves_order(tmp_path):
    frame = sample_frame()
    selected, results = train_models(frame)
    artifact, metadata = save_model(selected, results[selected], tmp_path)
    policy = tmp_path / "policy.yaml"
    policy.write_text("""policy_version: 'test'\nlevels:\n  low: {min_score: 0.0, max_score: 0.3, alert: false, action: none}\n  medium: {min_score: 0.3, max_score: 0.6, alert: false, action: monitor}\n  high: {min_score: 0.6, max_score: 0.85, alert: true, action: review}\n  critical: {min_score: 0.85, max_score: 1.0000001, alert: true, action: investigate}\n""", encoding="utf-8")
    scored = score_transactions(frame.iloc[:12], artifact, metadata, policy)
    assert scored.TransactionKey.tolist() == frame.TransactionKey.iloc[:12].tolist()
    assert scored.FraudScore.between(0, 1).all()
    assert set(scored.RiskLevel) <= {"LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_unknown_and_null_transaction_types_are_supported(tmp_path):
    frame = sample_frame(); selected, results = train_models(frame)
    artifact, metadata = save_model(selected, results[selected], tmp_path)
    policy = tmp_path / "policy.yaml"
    policy.write_text("""policy_version: 'test'\nlevels:\n  low: {min_score: 0.0, max_score: 0.3, alert: false, action: none}\n  medium: {min_score: 0.3, max_score: 0.6, alert: false, action: monitor}\n  high: {min_score: 0.6, max_score: 0.85, alert: true, action: review}\n  critical: {min_score: 0.85, max_score: 1.0000001, alert: true, action: investigate}\n""")
    candidate = frame.iloc[:2].copy(); candidate["type"] = ["NEW_TYPE", None]
    scored = score_transactions(candidate, artifact, metadata, policy)
    assert len(scored) == 2 and scored.FraudScore.between(0, 1).all()


def test_business_rule_baseline_and_metric_contract():
    selected, results = train_models(sample_frame())
    assert "baseline_rule" in results
    assert results["baseline_rule"]["pipeline"].predict_proba(
        build_features(sample_frame().iloc[:4])
    ).shape == (4, 2)
    metrics = evaluate_scores([0, 1], [0.1, 0.9], 0.5, amounts=[10, 25])
    required = {
        "pr_auc", "precision", "recall", "f2", "tn", "fp", "fn", "tp",
        "alert_count", "fraud_amount_captured", "fraud_amount_missed",
        "fraud_amount_capture_rate",
    }
    assert required <= metrics.keys()
