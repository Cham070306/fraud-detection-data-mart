/* =============================================================
   10_create_dashboard_objects.sql
   TV5 - BI/Dashboard objects:
   - Feedback columns on fact.FactAlert (analyst review loop)
   - Fix AlertStatus constraint to accept 'NEW' (scoring pipeline)
   - BI views: vw_AlertQueue, vw_TransactionAnalysis,
     vw_AlertFeedback, vw_ETLQualitySummary
   Idempotent: safe to re-run.
   ============================================================= */

USE FraudDW;
GO

/* ---------------------------------------------------------
   1a. Feedback columns on fact.FactAlert
   --------------------------------------------------------- */
IF NOT EXISTS (SELECT 1 FROM sys.columns
               WHERE object_id = OBJECT_ID(N'fact.FactAlert')
                 AND name = N'AnalystDecision')
BEGIN
    ALTER TABLE fact.FactAlert ADD
        AnalystDecision    VARCHAR(20)   NULL,
        FeedbackComment    NVARCHAR(500) NULL,
        ReviewedBy         NVARCHAR(100) NULL,
        ReviewedAt         DATETIME2     NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints
               WHERE name = N'CK_FactAlert_Decision'
                 AND parent_object_id = OBJECT_ID(N'fact.FactAlert'))
BEGIN
    ALTER TABLE fact.FactAlert ADD CONSTRAINT CK_FactAlert_Decision
        CHECK (AnalystDecision IN ('CONFIRMED_FRAUD','FALSE_POSITIVE','UNDER_INVESTIGATION'));
END
GO

/* ---------------------------------------------------------
   1b. Fix AlertStatus constraint: add 'NEW'
   (scoring pipeline emits AlertStatus='NEW' on load)
   --------------------------------------------------------- */
IF EXISTS (SELECT 1 FROM sys.check_constraints
           WHERE name = N'CK_FactAlert_Status'
             AND parent_object_id = OBJECT_ID(N'fact.FactAlert'))
BEGIN
    ALTER TABLE fact.FactAlert DROP CONSTRAINT CK_FactAlert_Status;
END
GO
ALTER TABLE fact.FactAlert ADD CONSTRAINT CK_FactAlert_Status
    CHECK (AlertStatus IN ('NEW','OPEN','IN_REVIEW','RESOLVED','FALSE_POSITIVE'));
GO

/* ---------------------------------------------------------
   1c. BI views
   --------------------------------------------------------- */

/* Alert queue: one row per HIGH/CRITICAL alert joined to its
   transaction + dims, for Streamlit/API/Power BI alert queue. */
CREATE OR ALTER VIEW bi.vw_AlertQueue AS
SELECT
    fa.AlertKey,
    fa.TransactionKey,
    fa.ScoreKey,
    fa.DateKey,
    d.StepDay,
    t.HourOfDay,
    tt.TypeCode,
    ft.Amount,
    ab.BandCode,
    a1.AccountID AS OrigAccountID,
    a2.AccountID AS DestAccountID,
    fa.FraudScore,
    rp.RiskLevel,
    fa.AlertLevel,
    fa.AlertStatus,
    rp.RecommendedAction,
    fa.AnalystDecision,
    fa.FeedbackComment,
    fa.ReviewedBy,
    fa.ReviewedAt,
    fa.CreatedAt
FROM fact.FactAlert fa
JOIN fact.FactTransaction ft ON fa.TransactionKey = ft.TransactionKey
JOIN dim.DimDate d ON fa.DateKey = d.DateKey
JOIN dim.DimTime t ON ft.TimeKey = t.TimeKey
JOIN dim.DimTransactionType tt ON ft.TransactionTypeKey = tt.TransactionTypeKey
JOIN dim.DimAmountBand ab ON ft.AmountBandKey = ab.AmountBandKey
JOIN dim.DimAccount a1 ON ft.OrigAccountKey = a1.AccountKey
JOIN dim.DimAccount a2 ON ft.DestAccountKey = a2.AccountKey
JOIN dim.DimRiskPolicy rp ON fa.RiskPolicyKey = rp.RiskPolicyKey;
GO

/* Transaction analysis: one row per transaction + optional model score
   (LEFT JOIN so drill-through works even without a score). */
CREATE OR ALTER VIEW bi.vw_TransactionAnalysis AS
SELECT
    ft.TransactionKey,
    ft.DateKey,
    d.StepDay,
    d.DayOfWeek,
    t.HourOfDay,
    t.TimeSlot,
    tt.TypeCode,
    ab.BandCode,
    ab.BandLabel,
    ft.Amount,
    ft.OldBalanceOrig,
    ft.NewBalanceOrig,
    ft.OldBalanceDest,
    ft.NewBalanceDest,
    ft.BalanceDropOrig,
    ft.IsFraud,
    ft.IsFlaggedFraud,
    a1.AccountID AS OrigAccountID,
    a1.AccountType AS OrigAccountType,
    a2.AccountID AS DestAccountID,
    a2.AccountType AS DestAccountType,
    ms.FraudScore,
    ms.RiskLevel,
    ms.IsPredictedFraud,
    ms.ScoredAt
FROM fact.FactTransaction ft
JOIN dim.DimDate d ON ft.DateKey = d.DateKey
JOIN dim.DimTime t ON ft.TimeKey = t.TimeKey
JOIN dim.DimTransactionType tt ON ft.TransactionTypeKey = tt.TransactionTypeKey
JOIN dim.DimAmountBand ab ON ft.AmountBandKey = ab.AmountBandKey
JOIN dim.DimAccount a1 ON ft.OrigAccountKey = a1.AccountKey
JOIN dim.DimAccount a2 ON ft.DestAccountKey = a2.AccountKey
LEFT JOIN fact.FactModelScore ms
    ON ms.TransactionKey = ft.TransactionKey;
GO

/* Alert feedback funnel for analyst decision reporting. */
CREATE OR ALTER VIEW bi.vw_AlertFeedback AS
SELECT
    fa.AlertKey,
    fa.DateKey,
    rp.RiskLevel,
    fa.AlertLevel,
    fa.AlertAmount,
    ft.IsFraud,
    fa.AnalystDecision,
    fa.AlertStatus,
    fa.ReviewedBy,
    fa.ReviewedAt
FROM fact.FactAlert fa
JOIN fact.FactTransaction ft ON fa.TransactionKey = ft.TransactionKey
JOIN dim.DimRiskPolicy rp ON fa.RiskPolicyKey = rp.RiskPolicyKey;
GO

/* ETL & DQ summary: per-batch reconciliation rate (KPI-Q01)
   and validation error rate (KPI-Q02). */
CREATE OR ALTER VIEW bi.vw_ETLQualitySummary AS
SELECT
    b.BatchID,
    b.SourceFileName,
    b.Status AS BatchStatus,
    b.StartedAt,
    b.FinishedAt,
    DATEDIFF(MINUTE, b.StartedAt, b.FinishedAt) AS DurationMinutes,
    r.ExpectedSourceRows AS SourceRows,
    r.FactRows,
    r.Status AS ReconStatus,
    r.ExpectedAmountSum,
    r.FactAmount,
    r.ExpectedFraudCount,
    r.FactFraudCount,
    CAST(r.FactRows * 1.0 / NULLIF(r.ExpectedSourceRows, 0) AS DECIMAL(10,4))
        AS ReconciliationRate,
    ISNULL(rej.RejectCount, 0) AS RejectCount,
    CAST(ISNULL(rej.RejectCount, 0) * 1.0 / NULLIF(r.ExpectedSourceRows, 0) AS DECIMAL(10,6))
        AS ValidationErrorRate
FROM audit.ETLBatchLog b
JOIN audit.ReconciliationLog r ON r.BatchID = b.BatchID
LEFT JOIN (
    SELECT BatchID, COUNT_BIG(*) AS RejectCount
    FROM audit.RejectLog
    GROUP BY BatchID
) rej ON rej.BatchID = b.BatchID;
GO

PRINT 'Da tao cac dashboard objects (10_create_dashboard_objects.sql)';
GO
