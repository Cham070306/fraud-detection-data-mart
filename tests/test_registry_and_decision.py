import json
import pandas as pd

from src.decision.alert_generator import generate_alerts
from src.scoring.idempotency import only_new_scores
from src.training.model_registry import register_model, resolve_model


def test_score_and_alert_idempotency():
    scored = pd.DataFrame({
        "TransactionKey":[1,1,2], "ModelVersion":["1","1","1"],
        "FraudScore":[.9,.9,.1], "RiskLevel":["CRITICAL","CRITICAL","LOW"],
        "AlertLevel":["CRITICAL","CRITICAL","NONE"], "AlertStatus":["NEW","NEW","NONE"],
        "RecommendedAction":["review","review","none"], "PolicyVersion":["1","1","1"],
        "ScoredAt":["now","now","now"], "CreateAlert":[True,True,False],
    })
    assert len(only_new_scores(scored)) == 2
    assert len(generate_alerts(scored)) == 1
    assert only_new_scores(scored, scored.iloc[[0]]).TransactionKey.tolist() == [2]


def test_registry_integrity(tmp_path):
    model = tmp_path / "model.joblib"; model.write_bytes(b"model")
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"model_name":"rf","version":"1","threshold":.3,"created_at":"now"}))
    registry = tmp_path / "registry.json"
    register_model(model, metadata, registry)
    assert resolve_model(registry_path=registry)["version"] == "1"
    model.write_bytes(b"tampered")
    import pytest
    with pytest.raises(ValueError, match="integrity"):
        resolve_model(registry_path=registry)
