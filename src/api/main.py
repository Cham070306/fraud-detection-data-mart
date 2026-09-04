from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.common.database import get_connection, execute, query
from src.common.config import AppConfig, PROJECT_ROOT
from src.api.schemas import (
    Alert,
    AlertFeedbackIn,
    AlertFeedbackOut,
    ConfusionMatrix,
    ETLQualityRow,
    HealthResponse,
    KPIOverview,
    ModelPerformanceRow,
)

app = FastAPI(
    title="Fraud Detection Data Mart API",
    version="1.0.0",
    description="REST API for PaySim Fraud Detection BI dashboard",
)


def _rows_to_dicts(rows: list, columns: list[str] | None = None) -> list[dict]:
    if not rows:
        return []
    if columns is None:
        columns = [desc[0] for desc in rows[0].cursor_description]
    return [dict(zip(columns, row)) for row in rows]


# ── Health ────────────────────────────────────────────────────

@app.get("/api/health", response_model=HealthResponse)
def health():
    try:
        conn = get_connection()
        try:
            query(conn, "SELECT 1")
            db_ok = True
        finally:
            conn.close()
    except Exception:
        db_ok = False

    active_version = None
    registry_path = PROJECT_ROOT / "models" / "registry.json"
    if registry_path.exists():
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        active_version = registry.get("active_version")

    return HealthResponse(
        status="ok",
        db_connected=db_ok,
        active_model_version=active_version,
    )


# ── Overview / KPIs ───────────────────────────────────────────

@app.get("/api/overview/kpis", response_model=KPIOverview)
def overview_kpis():
    conn = get_connection()
    try:
        rows = query(conn, """
            SELECT
                ISNULL(SUM(TransactionCount), 0) AS volume,
                ISNULL(SUM(TotalAmount), 0) AS amount,
                ISNULL(SUM(FraudCount), 0) AS fraud_count,
                ISNULL(SUM(FraudCount * TotalAmount / NULLIF(TransactionCount, 0)), 0)
                    AS fraud_amount
            FROM bi.vw_TransactionSummary
        """)
        d = _rows_to_dicts(rows, ["volume", "amount", "fraud_count", "fraud_amount"])[0]
        vol = int(d["volume"])
        amt = float(d["amount"])
        f_vol = int(d["fraud_count"])
        return KPIOverview(
            volume=vol,
            amount=amt,
            fraud_count=f_vol,
            fraud_amount=float(d["fraud_amount"]),
            fraud_rate_volume=f_vol / vol if vol else 0.0,
            fraud_rate_amount=float(d["fraud_amount"]) / amt if amt else 0.0,
        )
    finally:
        conn.close()


@app.get("/api/overview/trends")
def overview_trends(by: str = "day"):
    conn = get_connection()
    try:
        if by == "type":
            sql = """
                SELECT TypeCode AS label,
                       SUM(TransactionCount) AS volume,
                       SUM(FraudCount) AS fraud_count
                FROM bi.vw_TransactionSummary
                GROUP BY TypeCode ORDER BY volume DESC
            """
        else:
            sql = """
                SELECT StepDay AS label,
                       SUM(TransactionCount) AS volume,
                       SUM(FraudCount) AS fraud_count
                FROM bi.vw_TransactionSummary
                GROUP BY StepDay ORDER BY StepDay
            """
        rows = query(conn, sql)
        return _rows_to_dicts(rows, ["label", "volume", "fraud_count"])
    finally:
        conn.close()


# ── Transactions ──────────────────────────────────────────────

@app.get("/api/transactions", response_model=list[dict])
def list_transactions(limit: int = 100, fraud_only: bool = False):
    conn = get_connection()
    try:
        where = "WHERE ft.IsFraud = 1" if fraud_only else ""
        sql = f"""
            SELECT TOP {limit}
                TransactionKey, DateKey, StepDay, TypeCode,
                Amount, IsFraud,
                OrigAccountID, DestAccountID,
                FraudScore, RiskLevel
            FROM bi.vw_TransactionAnalysis
            {where}
            ORDER BY TransactionKey DESC
        """
        rows = query(conn, sql)
        return _rows_to_dicts(rows)
    finally:
        conn.close()


@app.get("/api/transactions/{transaction_key}")
def get_transaction(transaction_key: int):
    conn = get_connection()
    try:
        rows = query(conn, """
            SELECT *
            FROM bi.vw_TransactionAnalysis
            WHERE TransactionKey = ?
        """, (transaction_key,))
        if not rows:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return _rows_to_dicts(rows)[0]
    finally:
        conn.close()


# ── Alerts ────────────────────────────────────────────────────

@app.get("/api/alerts", response_model=list[dict])
def list_alerts(
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    conn = get_connection()
    try:
        conditions = []
        params = []
        if risk_level:
            conditions.append("RiskLevel = ?")
            params.append(risk_level.upper())
        if status:
            conditions.append("AlertStatus = ?")
            params.append(status.upper())
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"""
            SELECT TOP {limit}
                AlertKey, TransactionKey, DateKey, StepDay,
                TypeCode, Amount, FraudScore, RiskLevel,
                AlertLevel, AlertStatus, RecommendedAction,
                AnalystDecision, FeedbackComment, ReviewedBy,
                CONVERT(VARCHAR(19), ReviewedAt, 120) AS ReviewedAt
            FROM bi.vw_AlertQueue
            {where}
            ORDER BY
                CASE AlertLevel WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 END,
                FraudScore DESC
        """
        rows = query(conn, sql, tuple(params))
        return _rows_to_dicts(rows)
    finally:
        conn.close()


@app.post("/api/alerts/{alert_key}/feedback", response_model=AlertFeedbackOut)
def submit_feedback(alert_key: int, body: AlertFeedbackIn):
    status_map = {
        "CONFIRMED_FRAUD": "RESOLVED",
        "FALSE_POSITIVE": "FALSE_POSITIVE",
        "UNDER_INVESTIGATION": "IN_REVIEW",
    }
    new_status = status_map[body.decision]
    conn = get_connection()
    try:
        execute(conn, """
            UPDATE fact.FactAlert
            SET AnalystDecision = ?,
                AlertStatus = ?,
                FeedbackComment = ?,
                ReviewedBy = ?,
                ReviewedAt = SYSDATETIME()
            WHERE AlertKey = ?
        """, (body.decision, new_status, body.comment, body.reviewed_by, alert_key))
        rows = query(conn, """
            SELECT AlertKey, AnalystDecision, AlertStatus, ReviewedBy,
                   CONVERT(VARCHAR(19), ReviewedAt, 120) AS ReviewedAt
            FROM fact.FactAlert WHERE AlertKey = ?
        """, (alert_key,))
        if not rows:
            raise HTTPException(status_code=404, detail="Alert not found")
        d = _rows_to_dicts(rows)[0]
        return AlertFeedbackOut(
            alert_key=d["AlertKey"],
            decision=d["AnalystDecision"] or "",
            alert_status=d["AlertStatus"],
            reviewed_by=d.get("ReviewedBy"),
            reviewed_at=d.get("ReviewedAt"),
        )
    finally:
        conn.close()


# ── Model Performance ─────────────────────────────────────────

@app.get("/api/model/performance", response_model=list[dict])
def model_performance():
    conn = get_connection()
    try:
        rows = query(conn, """
            SELECT
                mv.ModelName,
                mv.Version AS model_version,
                rp.PolicyVersion,
                mv.Precision AS model_precision,
                mv.Recall AS model_recall,
                mv.F2Score,
                mv.PrAUC,
                mv.Threshold
            FROM dim.DimModelVersion mv
            CROSS JOIN dim.DimRiskPolicy rp
            WHERE mv.IsProduction = 1 AND rp.IsActive = 1
            GROUP BY mv.ModelName, mv.Version, rp.PolicyVersion,
                     mv.Precision, mv.Recall, mv.F2Score, mv.PrAUC, mv.Threshold
        """)
        return _rows_to_dicts(rows)
    finally:
        conn.close()


@app.get("/api/model/confusion", response_model=list[dict])
def model_confusion():
    """Confusion matrix from the model metadata file (authoritative)."""
    meta_path = PROJECT_ROOT / "models" / "fraud_model_v1.0.0_metadata.json"
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="Model metadata not found")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    tm = meta.get("test_metrics", meta.get("validation_metrics", {}))
    return [{
        "model_version": meta.get("version", "1.0.0"),
        "tn": tm.get("tn", 0),
        "fp": tm.get("fp", 0),
        "fn": tm.get("fn", 0),
        "tp": tm.get("tp", 0),
    }]


# ── Operations / ETL Quality ──────────────────────────────────

@app.get("/api/operations/etl", response_model=list[dict])
def operations_etl():
    conn = get_connection()
    try:
        rows = query(conn, """
            SELECT
                BatchID AS batch_id,
                SourceFileName AS source_file,
                BatchStatus AS batch_status,
                SourceRows AS source_rows,
                FactRows AS fact_rows,
                ReconStatus AS recon_status,
                ReconciliationRate AS reconciliation_rate,
                RejectCount AS reject_count,
                ValidationErrorRate AS validation_error_rate
            FROM bi.vw_ETLQualitySummary
            ORDER BY BatchID DESC
        """)
        return _rows_to_dicts(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
