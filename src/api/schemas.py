from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    active_model_version: Optional[str] = None


class KPIOverview(BaseModel):
    volume: int
    amount: float
    fraud_count: int
    fraud_amount: float
    fraud_rate_volume: float
    fraud_rate_amount: float


class TransactionRow(BaseModel):
    transaction_key: int
    date_key: int
    step_day: int
    type_code: str
    amount: float
    is_fraud: bool
    fraud_score: Optional[float] = None
    risk_level: Optional[str] = None


class Alert(BaseModel):
    alert_key: int
    transaction_key: int
    date_key: int
    step_day: int
    type_code: str
    amount: float
    fraud_score: float
    risk_level: str
    alert_level: str
    alert_status: str
    recommended_action: str
    analyst_decision: Optional[str] = None
    feedback_comment: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


class AlertFeedbackIn(BaseModel):
    decision: Literal["CONFIRMED_FRAUD", "FALSE_POSITIVE", "UNDER_INVESTIGATION"]
    comment: Optional[str] = Field(default=None, max_length=500)
    reviewed_by: Optional[str] = Field(default=None, max_length=100)


class AlertFeedbackOut(BaseModel):
    alert_key: int
    decision: str
    alert_status: str
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None


class ModelPerformanceRow(BaseModel):
    model_name: str
    version: str
    policy_version: str
    precision: float
    recall: float
    f2: float
    pr_auc: float
    threshold: float
    alerts_per_1000: Optional[float] = None
    capture_rate: Optional[float] = None


class ConfusionMatrix(BaseModel):
    model_version: str
    tn: int
    fp: int
    fn: int
    tp: int


class ETLQualityRow(BaseModel):
    batch_id: int
    source_file: str
    batch_status: str
    source_rows: int
    fact_rows: int
    recon_status: str
    reconciliation_rate: float
    reject_count: int
    validation_error_rate: float
