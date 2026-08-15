/* =============================================================
   08_validation_queries.sql
   Validation queries for ETL and DW
   ============================================================= */

USE FraudDW;
GO

-- Row count checks
SELECT 'stg.TransactionRaw' AS TableName, COUNT_BIG(*) AS RowCount FROM stg.TransactionRaw
UNION ALL
SELECT 'fact.FactTransaction', COUNT_BIG(*) FROM fact.FactTransaction
UNION ALL
SELECT 'fact.FactModelScore', COUNT_BIG(*) FROM fact.FactModelScore
UNION ALL
SELECT 'fact.FactAlert', COUNT_BIG(*) FROM fact.FactAlert;
GO

-- Fraud count check in fact
SELECT IsFraud, COUNT_BIG(*) AS Cnt
FROM fact.FactTransaction
GROUP BY IsFraud;
GO

-- EDA-01 independent reconciliation (run by the DW/ETL owner after full load)
-- Expected for the standard PaySim file: 6,362,620 / 8,213 / 16.
SELECT
    COUNT_BIG(*) AS TotalRows,
    SUM(CASE WHEN IsFraud = 1 THEN 1 ELSE 0 END) AS FraudRows,
    SUM(CASE WHEN IsFlaggedFraud = 1 THEN 1 ELSE 0 END) AS FlaggedFraudRows
FROM fact.FactTransaction;
GO

-- Amount reconciliation
SELECT
    SUM(Amount) AS TotalAmount,
    SUM(CASE WHEN IsFraud = 1 THEN Amount ELSE 0 END) AS FraudAmount
FROM fact.FactTransaction;
GO

-- Orphan checks
SELECT TOP 10 f.TransactionKey
FROM fact.FactTransaction f
LEFT JOIN dim.DimDate d ON f.DateKey = d.DateKey
WHERE d.DateKey IS NULL;
GO

-- Required-field, domain and sign checks (all results must be zero)
SELECT
    SUM(CASE WHEN StepRaw IS NULL OR TypeCode IS NULL OR Amount IS NULL
                  OR NameOrig IS NULL OR NameDest IS NULL
                  OR IsFraud IS NULL OR IsFlaggedFraud IS NULL THEN 1 ELSE 0 END) AS RequiredNullRows,
    SUM(CASE WHEN TypeCode NOT IN ('CASH_IN','CASH_OUT','DEBIT','PAYMENT','TRANSFER') THEN 1 ELSE 0 END) AS InvalidTypeRows,
    SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END) AS NegativeAmountRows
FROM stg.TransactionRaw;
GO

-- Reject and source accounting by batch
SELECT b.BatchID, b.Status,
       COUNT(DISTINCT s.RowNumberInChunk) AS StagingRows,
       COUNT(DISTINCT r.RejectID) AS RejectedRows
FROM audit.ETLBatchLog b
LEFT JOIN stg.TransactionRaw s ON s.BatchID = b.BatchID
LEFT JOIN audit.RejectLog r ON r.BatchID = b.BatchID
GROUP BY b.BatchID, b.Status
ORDER BY b.BatchID DESC;
GO

-- Business duplicates in fact; duplicate groups must be zero for PaySim.
SELECT COUNT_BIG(*) AS DuplicateGroups
FROM (
    SELECT StepRaw, TransactionTypeKey, OrigAccountKey, DestAccountKey, Amount,
           OldBalanceOrig, NewBalanceOrig, OldBalanceDest, NewBalanceDest,
           IsFraud, IsFlaggedFraud
    FROM fact.FactTransaction
    GROUP BY StepRaw, TransactionTypeKey, OrigAccountKey, DestAccountKey, Amount,
             OldBalanceOrig, NewBalanceOrig, OldBalanceDest, NewBalanceDest,
             IsFraud, IsFlaggedFraud
    HAVING COUNT_BIG(*) > 1
) AS duplicates;
GO

-- All six FK orphan counts must be zero.
SELECT
 SUM(CASE WHEN d.DateKey IS NULL THEN 1 ELSE 0 END) AS DateOrphans,
 SUM(CASE WHEN t.TimeKey IS NULL THEN 1 ELSE 0 END) AS TimeOrphans,
 SUM(CASE WHEN tt.TransactionTypeKey IS NULL THEN 1 ELSE 0 END) AS TypeOrphans,
 SUM(CASE WHEN oa.AccountKey IS NULL THEN 1 ELSE 0 END) AS OrigAccountOrphans,
 SUM(CASE WHEN da.AccountKey IS NULL THEN 1 ELSE 0 END) AS DestAccountOrphans,
 SUM(CASE WHEN ab.AmountBandKey IS NULL THEN 1 ELSE 0 END) AS AmountBandOrphans
FROM fact.FactTransaction f
LEFT JOIN dim.DimDate d ON d.DateKey=f.DateKey
LEFT JOIN dim.DimTime t ON t.TimeKey=f.TimeKey
LEFT JOIN dim.DimTransactionType tt ON tt.TransactionTypeKey=f.TransactionTypeKey
LEFT JOIN dim.DimAccount oa ON oa.AccountKey=f.OrigAccountKey
LEFT JOIN dim.DimAccount da ON da.AccountKey=f.DestAccountKey
LEFT JOIN dim.DimAmountBand ab ON ab.AmountBandKey=f.AmountBandKey;
GO
