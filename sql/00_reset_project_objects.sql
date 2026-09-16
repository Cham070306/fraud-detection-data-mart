/* Destructive reset used only by scripts/setup_database.ps1 -Rebuild. */
USE FraudDW;
GO

DROP VIEW IF EXISTS bi.vw_AlertFeedback;
DROP VIEW IF EXISTS bi.vw_AlertQueue;
DROP VIEW IF EXISTS bi.vw_TransactionAnalysis;
DROP VIEW IF EXISTS bi.vw_ETLQualitySummary;
DROP VIEW IF EXISTS bi.vw_TransactionSummary;
DROP VIEW IF EXISTS bi.vw_FraudAnalysis;
DROP VIEW IF EXISTS bi.vw_ModelPerformance;
DROP VIEW IF EXISTS bi.vw_AlertSummary;
DROP VIEW IF EXISTS bi.vw_ETLQuality;
GO

DROP TABLE IF EXISTS fact.FactAlert;
DROP TABLE IF EXISTS fact.FactModelScore;
DROP TABLE IF EXISTS fact.FactTransaction;
GO

DROP TABLE IF EXISTS dim.DimModelVersion;
DROP TABLE IF EXISTS dim.DimRiskPolicy;
DROP TABLE IF EXISTS dim.DimAmountBand;
DROP TABLE IF EXISTS dim.DimAccount;
DROP TABLE IF EXISTS dim.DimTransactionType;
DROP TABLE IF EXISTS dim.DimTime;
DROP TABLE IF EXISTS dim.DimDate;
GO

DROP TABLE IF EXISTS stg.TransactionRaw;
DROP TABLE IF EXISTS audit.ReconciliationLog;
DROP TABLE IF EXISTS audit.RejectLog;
DROP TABLE IF EXISTS audit.ETLBatchLog;
GO
