import pandas as pd
import pytest

from src.etl.load_ml_results import normalize_chunk


def valid_score_frame():
    return pd.DataFrame([{
        "TransactionKey": 1, "DateKey": 20230101, "Amount": 100.0,
        "FraudScore": 0.9, "PredictedFraud": 1, "RiskLevel": "critical",
        "CreateAlert": True, "RecommendedAction": "BLOCK_AND_ALERT",
        "ModelVersion": "1.0.0", "PolicyVersion": "1.0.0",
        "ScoredAt": "2026-08-16T15:10:52+00:00",
    }])


def test_normalize_score_chunk():
    result = normalize_chunk(valid_score_frame())
    assert result.loc[0, "TransactionKey"] == 1
    assert result.loc[0, "RiskLevel"] == "CRITICAL"
    assert result.loc[0, "FraudScore"] == 0.9


def test_normalize_score_rejects_out_of_range_score():
    frame = valid_score_frame()
    frame.loc[0, "FraudScore"] = 1.1
    with pytest.raises(ValueError, match="FraudScore"):
        normalize_chunk(frame)


def test_normalize_score_parses_false_strings():
    frame = valid_score_frame()
    frame["PredictedFraud"] = frame["PredictedFraud"].astype(object)
    frame["CreateAlert"] = frame["CreateAlert"].astype(object)
    frame.loc[0, "PredictedFraud"] = "false"
    frame.loc[0, "CreateAlert"] = "0"
    result = normalize_chunk(frame)
    assert bool(result.loc[0, "PredictedFraud"]) is False
    assert bool(result.loc[0, "CreateAlert"]) is False
