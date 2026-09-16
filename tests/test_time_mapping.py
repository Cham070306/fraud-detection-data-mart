import pandas as pd
import numpy as np
import pytest

from src.common.time_mapping import derive_simulation_time
from src.features.build_features import build_features
from src.scoring.score import score_transactions


def test_shared_time_mapping_boundaries():
    result = derive_simulation_time(pd.Series([1, 24, 25, 743]), "2023-01-01")
    assert result["StepDay"].tolist() == [1, 1, 2, 31]
    assert result["TimeKey"].tolist() == [0, 23, 0, 22]
    assert result["DateKey"].tolist() == [20230101, 20230101, 20230102, 20230131]


def test_ml_time_features_match_dw_mapping():
    frame = pd.DataFrame({
        "step": [1, 24, 25], "type": ["PAYMENT"] * 3, "amount": [10.0] * 3,
        "oldbalanceOrg": [10.0] * 3, "newbalanceOrig": [0.0] * 3,
        "oldbalanceDest": [0.0] * 3, "newbalanceDest": [10.0] * 3,
    })
    features = build_features(frame)
    assert features["Hour"].tolist() == [0, 23, 0]
    assert features["Day"].tolist() == [1, 1, 2]


def test_production_scoring_requires_transaction_key(monkeypatch):
    class FakeModel:
        def predict_proba(self, frame):
            return np.array([[0.9, 0.1] for _ in range(len(frame))])

    monkeypatch.setattr("src.scoring.score.joblib.load", lambda _path: FakeModel())
    frame = pd.DataFrame({
        "step": [1], "type": ["PAYMENT"], "amount": [10.0],
        "oldbalanceOrg": [10.0], "newbalanceOrig": [0.0],
        "oldbalanceDest": [0.0], "newbalanceDest": [10.0],
    })
    metadata = {"feature_list": [], "threshold": 0.32, "version": "1.0.0"}
    with pytest.raises(ValueError, match="TransactionKey"):
        score_transactions(frame, "unused.joblib", metadata, "configs/risk_policy.yaml")
