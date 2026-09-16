/* Idempotent migration for ML metadata and score/alert natural keys. */
USE FraudDW;
GO

IF EXISTS (
    SELECT 1 FROM fact.FactModelScore
    GROUP BY TransactionKey, ModelVersionKey
    HAVING COUNT_BIG(*) > 1
)
    THROW 51010, 'Duplicate FactModelScore business keys exist.', 1;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'fact.FactModelScore')
      AND name = N'UX_FactModelScore_TransactionModel'
)
BEGIN
    CREATE UNIQUE INDEX UX_FactModelScore_TransactionModel
    ON fact.FactModelScore(TransactionKey, ModelVersionKey);
END;
GO

IF EXISTS (SELECT 1 FROM fact.FactAlert GROUP BY ScoreKey HAVING COUNT_BIG(*) > 1)
    THROW 51011, 'Duplicate FactAlert ScoreKey values exist.', 1;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID(N'fact.FactAlert')
      AND name = N'UX_FactAlert_Score'
)
BEGIN
    CREATE UNIQUE INDEX UX_FactAlert_Score ON fact.FactAlert(ScoreKey);
END;
GO

IF NOT EXISTS (SELECT 1 FROM dim.DimRiskPolicy WHERE PolicyVersion = '1.0.0')
BEGIN
    UPDATE dim.DimRiskPolicy
    SET PolicyVersion = '1.0.0'
    WHERE PolicyVersion = 'v1.0';
END;
GO

UPDATE dim.DimModelVersion
SET ModelName = 'RandomForest', Version = '1.0.0',
    Precision = 0.9992, Recall = 0.9992, F2Score = 0.9992,
    PrAUC = 1.0000, Threshold = 0.3200, IsProduction = 1,
    ModelFilePath = 'models/fraud_model_v1.0.0.joblib'
WHERE ModelVersionKey = 1;
GO
