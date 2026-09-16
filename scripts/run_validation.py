#!/usr/bin/env python
"""Validate the operational FraudDW and return a non-zero code on failure."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.database import get_connection, query


def scalar(conn, sql: str) -> int:
    return int(query(conn, sql)[0][0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-transactions", type=int, default=6_362_620)
    parser.add_argument("--expected-fraud", type=int, default=8_213)
    parser.add_argument("--expected-alerts", type=int, default=8_218)
    parser.add_argument("--require-ml", action="store_true")
    args = parser.parse_args()

    conn = get_connection()
    try:
        result = {
            "staging_rows": scalar(conn, """
                SELECT COUNT_BIG(*) FROM stg.TransactionRaw
                WHERE BatchID = (SELECT MAX(BatchID) FROM audit.ETLBatchLog)
            """),
            "fact_rows": scalar(conn, "SELECT COUNT_BIG(*) FROM fact.FactTransaction"),
            "fraud_rows": scalar(conn, "SELECT COUNT_BIG(*) FROM fact.FactTransaction WHERE IsFraud=1"),
            "score_rows": scalar(conn, """
                SELECT COUNT_BIG(*) FROM fact.FactModelScore s
                JOIN dim.DimModelVersion m ON m.ModelVersionKey=s.ModelVersionKey
                WHERE m.IsProduction=1
            """),
            "alert_rows": scalar(conn, """
                SELECT COUNT_BIG(*) FROM fact.FactAlert a
                JOIN fact.FactModelScore s ON s.ScoreKey=a.ScoreKey
                JOIN dim.DimModelVersion m ON m.ModelVersionKey=s.ModelVersionKey
                WHERE m.IsProduction=1
            """),
            "duplicate_groups": scalar(conn, """
                SELECT COUNT_BIG(*) FROM (
                    SELECT DateKey, TimeKey, TransactionTypeKey, OrigAccountKey,
                           DestAccountKey, AmountBandKey, StepRaw, Amount,
                           OldBalanceOrig, NewBalanceOrig, OldBalanceDest,
                           NewBalanceDest, IsFraud, IsFlaggedFraud
                    FROM fact.FactTransaction
                    GROUP BY DateKey, TimeKey, TransactionTypeKey, OrigAccountKey,
                             DestAccountKey, AmountBandKey, StepRaw, Amount,
                             OldBalanceOrig, NewBalanceOrig, OldBalanceDest,
                             NewBalanceDest, IsFraud, IsFlaggedFraud
                    HAVING COUNT_BIG(*) > 1
                ) d
            """),
            "orphan_rows": scalar(conn, """
                SELECT COUNT_BIG(*) FROM fact.FactTransaction f
                LEFT JOIN dim.DimDate d ON d.DateKey=f.DateKey
                LEFT JOIN dim.DimTime t ON t.TimeKey=f.TimeKey
                LEFT JOIN dim.DimTransactionType tt ON tt.TransactionTypeKey=f.TransactionTypeKey
                LEFT JOIN dim.DimAccount oa ON oa.AccountKey=f.OrigAccountKey
                LEFT JOIN dim.DimAccount da ON da.AccountKey=f.DestAccountKey
                LEFT JOIN dim.DimAmountBand ab ON ab.AmountBandKey=f.AmountBandKey
                WHERE d.DateKey IS NULL OR t.TimeKey IS NULL OR tt.TransactionTypeKey IS NULL
                   OR oa.AccountKey IS NULL OR da.AccountKey IS NULL OR ab.AmountBandKey IS NULL
            """),
            "time_mapping_errors": scalar(conn, """
                SELECT COUNT_BIG(*) FROM fact.FactTransaction
                WHERE TimeKey <> (StepRaw - 1) % 24
                   OR DateKey <> CONVERT(INT, CONVERT(CHAR(8),
                       DATEADD(DAY, (StepRaw - 1) / 24, '2023-01-01'), 112))
            """),
        }
        failures = []
        for field in ("staging_rows", "fact_rows"):
            if result[field] != args.expected_transactions:
                failures.append(f"{field} expected {args.expected_transactions}, got {result[field]}")
        if result["fraud_rows"] != args.expected_fraud:
            failures.append(f"fraud_rows expected {args.expected_fraud}, got {result['fraud_rows']}")
        for field in ("duplicate_groups", "orphan_rows", "time_mapping_errors"):
            if result[field] != 0:
                failures.append(f"{field} expected 0, got {result[field]}")
        if args.require_ml:
            if result["score_rows"] != args.expected_transactions:
                failures.append(
                    f"score_rows expected {args.expected_transactions}, got {result['score_rows']}"
                )
            if result["alert_rows"] != args.expected_alerts:
                failures.append(
                    f"alert_rows expected {args.expected_alerts}, got {result['alert_rows']}"
                )
        result["status"] = "PASS" if not failures else "FAIL"
        result["failures"] = failures
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if not failures else 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
