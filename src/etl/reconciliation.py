from __future__ import annotations
from src.common.logger import get_logger
from src.common.database import query, execute

logger = get_logger("etl.reconciliation")


def reconcile(conn, batch_id, expected_source_rows, expected_amount_sum, expected_fraud_count):
    """Doi soat sau ETL cho fact transaction."""
    fact_rows = query(conn, "SELECT COUNT_BIG(*) FROM fact.FactTransaction")[0][0]
    fact_amount = query(conn, "SELECT SUM(Amount) FROM fact.FactTransaction")[0][0] or 0.0
    fact_fraud = query(conn, "SELECT COUNT_BIG(*) FROM fact.FactTransaction WHERE IsFraud = 1")[0][0]

    result = {
        "batch_id": batch_id,
        "fact_rows": int(fact_rows),
        "fact_amount": float(fact_amount),
        "fact_fraud_count": int(fact_fraud),
        "expected_source_rows": int(expected_source_rows),
        "expected_amount_sum": float(expected_amount_sum),
        "expected_fraud_count": int(expected_fraud_count),
        "row_count_match": int(fact_rows) == int(expected_source_rows),
        "amount_match": abs(float(fact_amount) - float(expected_amount_sum)) < 0.01,
        "fraud_match": int(fact_fraud) == int(expected_fraud_count),
    }
    result["status"] = "PASS" if (result["row_count_match"] and result["fraud_match"]) else "FAIL"
    logger.info(f"Reconciliation batch {batch_id}: {result}")
    return result


def log_reconciliation(conn, result):
    execute(
        conn,
        (
            "INSERT INTO audit.ReconciliationLog ("
            " BatchID, FactRows, FactAmount, FactFraudCount,"
            " ExpectedSourceRows, ExpectedAmountSum, ExpectedFraudCount, Status"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        (
            result["batch_id"],
            result["fact_rows"],
            result["fact_amount"],
            result["fact_fraud_count"],
            result["expected_source_rows"],
            result["expected_amount_sum"],
            result["expected_fraud_count"],
            result["status"],
        ),
    )
