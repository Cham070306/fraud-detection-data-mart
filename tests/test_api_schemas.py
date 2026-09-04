import pytest
from pydantic import ValidationError

from src.api.schemas import (
    AlertFeedbackIn,
    AlertFeedbackOut,
    HealthResponse,
    KPIOverview,
)


def test_health_response_accepts_optional_model():
    h = HealthResponse(status="ok", db_connected=True, active_model_version="1.0.0")
    assert h.status == "ok" and h.db_connected and h.active_model_version == "1.0.0"


def test_kpi_overview_round_trip():
    k = KPIOverview(
        volume=6_362_620, amount=1_144_392_944_759.77,
        fraud_count=8213, fraud_amount=12_056_415_427.84,
        fraud_rate_volume=0.00129, fraud_rate_amount=0.01054,
    )
    assert k.fraud_count == 8213


def test_alert_feedback_accepts_valid_decisions():
    for decision in ["CONFIRMED_FRAUD", "FALSE_POSITIVE", "UNDER_INVESTIGATION"]:
        fb = AlertFeedbackIn(decision=decision, reviewed_by="analyst")
        assert fb.decision == decision


def test_alert_feedback_rejects_invalid_decision():
    with pytest.raises(ValidationError):
        AlertFeedbackIn(decision="MAYBE")


def test_alert_feedback_rejects_overlong_comment():
    with pytest.raises(ValidationError):
        AlertFeedbackIn(decision="CONFIRMED_FRAUD", comment="x" * 501)


def test_alert_feedback_out_fields():
    out = AlertFeedbackOut(
        alert_key=1, decision="CONFIRMED_FRAUD",
        alert_status="RESOLVED", reviewed_by="analyst", reviewed_at="2026-09-04 10:00:00",
    )
    assert out.alert_status == "RESOLVED"
