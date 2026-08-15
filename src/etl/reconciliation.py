from __future__ import annotations

from src.common.database import execute, query
from src.common.logger import get_logger

logger = get_logger("etl.reconciliation")

_BATCH_FACTS_CTE = """
WITH ValidSource AS (
    SELECT s.StepRaw, s.TypeCode, s.Amount, s.NameOrig, s.OldBalanceOrg,
           s.NewBalanceOrig, s.NameDest, s.OldBalanceDest, s.NewBalanceDest,
           s.IsFraud, s.IsFlaggedFraud
    FROM stg.TransactionRaw AS s
    WHERE s.BatchID = ? AND s.StepRaw >= 1
      AND s.TypeCode IN ('CASH_IN','CASH_OUT','DEBIT','PAYMENT','TRANSFER')
      AND s.Amount >= 0 AND s.IsFraud IN (0,1) AND s.IsFlaggedFraud IN (0,1)
      AND LEN(s.NameOrig) BETWEEN 2 AND 20 AND LEN(s.NameDest) BETWEEN 2 AND 20
      AND LEFT(s.NameOrig,1) IN ('C','M') AND LEFT(s.NameDest,1) IN ('C','M')
      AND SUBSTRING(s.NameOrig,2,20) NOT LIKE '%[^0-9]%'
      AND SUBSTRING(s.NameDest,2,20) NOT LIKE '%[^0-9]%'
), BatchFacts AS (
    SELECT DISTINCT f.TransactionKey, f.Amount, f.IsFraud
    FROM ValidSource AS s
    JOIN dim.DimTransactionType AS tt ON tt.TypeCode = s.TypeCode
    JOIN dim.DimAccount AS oa ON oa.AccountID = s.NameOrig
    JOIN dim.DimAccount AS da ON da.AccountID = s.NameDest
    JOIN fact.FactTransaction AS f
      ON f.StepRaw = s.StepRaw AND f.TransactionTypeKey = tt.TransactionTypeKey
     AND f.OrigAccountKey = oa.AccountKey AND f.DestAccountKey = da.AccountKey
     AND f.Amount = s.Amount AND f.OldBalanceOrig = s.OldBalanceOrg
     AND f.NewBalanceOrig = s.NewBalanceOrig AND f.OldBalanceDest = s.OldBalanceDest
     AND f.NewBalanceDest = s.NewBalanceDest
     AND f.IsFraud = s.IsFraud AND f.IsFlaggedFraud = s.IsFlaggedFraud
)
"""


def reconcile(conn, batch_id, expected_source_rows, expected_amount_sum,
              expected_fraud_count, inserted_rows=0):
    """Reconcile facts matching this batch, including an idempotent re-run."""
    matched = query(
        conn,
        _BATCH_FACTS_CTE + """
SELECT COUNT_BIG(*), COALESCE(SUM(Amount), 0),
       COALESCE(SUM(CASE WHEN IsFraud=1 THEN 1 ELSE 0 END), 0)
FROM BatchFacts""",
        (batch_id,),
    )[0]
    duplicate_groups = query(
        conn,
        """SELECT COUNT_BIG(*) FROM (
 SELECT DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey,
        AmountBandKey, StepRaw, Amount, OldBalanceOrig, NewBalanceOrig,
        OldBalanceDest, NewBalanceDest, IsFraud, IsFlaggedFraud
 FROM fact.FactTransaction
 GROUP BY DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey,
          AmountBandKey, StepRaw, Amount, OldBalanceOrig, NewBalanceOrig,
          OldBalanceDest, NewBalanceDest, IsFraud, IsFlaggedFraud
 HAVING COUNT_BIG(*) > 1) AS duplicate_grains""",
    )[0][0]
    orphan_rows = query(
        conn,
        """SELECT COUNT_BIG(*) FROM fact.FactTransaction f
 LEFT JOIN dim.DimDate d ON d.DateKey=f.DateKey
 LEFT JOIN dim.DimTime t ON t.TimeKey=f.TimeKey
 LEFT JOIN dim.DimTransactionType tt ON tt.TransactionTypeKey=f.TransactionTypeKey
 LEFT JOIN dim.DimAccount oa ON oa.AccountKey=f.OrigAccountKey
 LEFT JOIN dim.DimAccount da ON da.AccountKey=f.DestAccountKey
 LEFT JOIN dim.DimAmountBand ab ON ab.AmountBandKey=f.AmountBandKey
 WHERE d.DateKey IS NULL OR t.TimeKey IS NULL OR tt.TransactionTypeKey IS NULL
    OR oa.AccountKey IS NULL OR da.AccountKey IS NULL OR ab.AmountBandKey IS NULL""",
    )[0][0]

    final_rows, fact_amount, fact_fraud = int(matched[0]), float(matched[1]), int(matched[2])
    inserted_rows = int(inserted_rows)
    existing_rows = final_rows - inserted_rows
    result = {
        "batch_id": int(batch_id), "source_rows": int(expected_source_rows),
        "valid_rows": int(expected_source_rows), "inserted_rows": inserted_rows,
        "existing_rows": existing_rows, "final_fact_rows": final_rows,
        "fact_rows": final_rows, "fact_amount": fact_amount,
        "fact_fraud_count": fact_fraud,
        "expected_source_rows": int(expected_source_rows),
        "expected_amount_sum": float(expected_amount_sum),
        "expected_fraud_count": int(expected_fraud_count),
        "duplicate_groups": int(duplicate_groups), "orphan_rows": int(orphan_rows),
        "row_count_match": final_rows == int(expected_source_rows),
        "load_accounting_match": existing_rows >= 0 and
                                 inserted_rows + existing_rows == int(expected_source_rows),
        "amount_match": abs(fact_amount - float(expected_amount_sum)) < 0.01,
        "fraud_match": fact_fraud == int(expected_fraud_count),
        "duplicate_free": int(duplicate_groups) == 0,
        "orphan_free": int(orphan_rows) == 0,
    }
    checks = ("row_count_match", "load_accounting_match", "amount_match", "fraud_match",
              "duplicate_free", "orphan_free")
    result["status"] = "PASS" if all(result[name] for name in checks) else "FAIL"
    logger.info("Reconciliation batch %s: %s", batch_id, result)
    return result


def log_reconciliation(conn, result):
    execute(
        conn,
        """INSERT INTO audit.ReconciliationLog (
 BatchID, FactRows, FactAmount, FactFraudCount,
 ExpectedSourceRows, ExpectedAmountSum, ExpectedFraudCount, Status)
 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (result["batch_id"], result["fact_rows"], result["fact_amount"],
         result["fact_fraud_count"], result["expected_source_rows"],
         result["expected_amount_sum"], result["expected_fraud_count"], result["status"]),
    )
