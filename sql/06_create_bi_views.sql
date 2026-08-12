/* =============================================================
   06_create_bi_views.sql
   5 BI views chuan hoa
   ============================================================= */

USE FraudDW;
GO

CREATE OR ALTER VIEW bi.vw_TransactionSummary AS
SELECT
    d.DateKey,
    d.StepDay,
    t.TimeKey,
    tt.TypeCode,
    COUNT_BIG(*) AS TransactionCount,
    SUM(f.Amount) AS TotalAmount,
    SUM(CASE WHEN f.IsFraud = 1 THEN 1 ELSE 0 END) AS FraudCount,
    CAST(SUM(CASE WHEN f.IsFraud = 1 THEN 1 ELSE 0 END) * 1.0 / NULLIF(COUNT_BIG(*),0) AS DECIMAL(10,6)) AS FraudRate
FROM fact.FactTransaction f
JOIN dim.DimDate d ON f.DateKey = d.DateKey
JOIN dim.DimTime t ON f.TimeKey = t.TimeKey
JOIN dim.DimTransactionType tt ON f.TransactionTypeKey = tt.TransactionTypeKey
GROUP BY d.DateKey, d.StepDay, t.TimeKey, tt.TypeCode;
GO

CREATE OR ALTER VIEW bi.vw_FraudAnalysis AS
SELECT
    d.DateKey,
    d.StepDay,
    t.TimeSlot,
    tt.TypeCode,
    ab.BandCode,
    ab.BandLabel,
    a1.AccountType AS OrigAccountType,
    a2.AccountType AS DestAccountType,
    COUNT_BIG(*) AS TransactionCount,
    SUM(CASE WHEN f.IsFraud = 1 THEN 1 ELSE 0 END) AS FraudCount,
    SUM(f.Amount) AS TotalAmount,
    SUM(f.BalanceDropOrig) AS TotalBalanceDropOrig
FROM fact.FactTransaction f
JOIN dim.DimDate d ON f.DateKey = d.DateKey
JOIN dim.DimTime t ON f.TimeKey = t.TimeKey
JOIN dim.DimTransactionType tt ON f.TransactionTypeKey = tt.TransactionTypeKey
JOIN dim.DimAmountBand ab ON f.AmountBandKey = ab.AmountBandKey
JOIN dim.DimAccount a1 ON f.OrigAccountKey = a1.AccountKey
JOIN dim.DimAccount a2 ON f.DestAccountKey = a2.AccountKey
GROUP BY d.DateKey, d.StepDay, t.TimeSlot, tt.TypeCode, ab.BandCode, ab.BandLabel, a1.AccountType, a2.AccountType;
GO

CREATE OR ALTER VIEW bi.vw_ModelPerformance AS
SELECT
    d.DateKey,
    mv.ModelName,
    mv.Version,
    rp.PolicyVersion,
    rp.RiskLevel,
    COUNT_BIG(*) AS ScoreCount,
    AVG(CAST(ms.FraudScore AS DECIMAL(18,6))) AS AvgFraudScore,
    SUM(CASE WHEN ms.IsPredictedFraud = 1 THEN 1 ELSE 0 END) AS PredictedFraudCount,
    SUM(CASE WHEN ft.IsFraud = 1 AND ms.IsPredictedFraud = 1 THEN 1 ELSE 0 END) AS TruePositiveCount
FROM fact.FactModelScore ms
JOIN fact.FactTransaction ft ON ms.TransactionKey = ft.TransactionKey
JOIN dim.DimDate d ON ms.DateKey = d.DateKey
JOIN dim.DimModelVersion mv ON ms.ModelVersionKey = mv.ModelVersionKey
JOIN dim.DimRiskPolicy rp ON ms.RiskPolicyKey = rp.RiskPolicyKey
GROUP BY d.DateKey, mv.ModelName, mv.Version, rp.PolicyVersion, rp.RiskLevel;
GO

CREATE OR ALTER VIEW bi.vw_AlertSummary AS
SELECT
    d.DateKey,
    rp.RiskLevel,
    fa.AlertLevel,
    fa.AlertStatus,
    COUNT_BIG(*) AS AlertCount,
    SUM(fa.AlertAmount) AS AlertAmount,
    AVG(fa.FraudScore) AS AvgFraudScore
FROM fact.FactAlert fa
JOIN dim.DimDate d ON fa.DateKey = d.DateKey
JOIN dim.DimRiskPolicy rp ON fa.RiskPolicyKey = rp.RiskPolicyKey
GROUP BY d.DateKey, rp.RiskLevel, fa.AlertLevel, fa.AlertStatus;
GO

CREATE OR ALTER VIEW bi.vw_ETLQuality AS
SELECT
    s.BatchID,
    s.SourceFileName,
    COUNT_BIG(*) AS StagingRows,
    SUM(CASE WHEN s.IsFraud = 1 THEN 1 ELSE 0 END) AS StagingFraudRows,
    MIN(s.LoadedAt) AS FirstLoadedAt,
    MAX(s.LoadedAt) AS LastLoadedAt
FROM stg.TransactionRaw s
GROUP BY s.BatchID, s.SourceFileName;
GO
