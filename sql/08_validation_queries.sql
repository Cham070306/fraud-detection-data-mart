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
