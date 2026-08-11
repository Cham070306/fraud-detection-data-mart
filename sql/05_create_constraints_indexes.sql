/* =============================================================
   05_create_constraints_indexes.sql
   PK/FK, check, index cho fact tables
   ============================================================= */

USE FraudDW;
GO

ALTER TABLE fact.FactTransaction
ADD CONSTRAINT FK_FactTransaction_DimDate FOREIGN KEY (DateKey) REFERENCES dim.DimDate(DateKey),
    CONSTRAINT FK_FactTransaction_DimTime FOREIGN KEY (TimeKey) REFERENCES dim.DimTime(TimeKey),
    CONSTRAINT FK_FactTransaction_DimType FOREIGN KEY (TransactionTypeKey) REFERENCES dim.DimTransactionType(TransactionTypeKey),
    CONSTRAINT FK_FactTransaction_OrigAccount FOREIGN KEY (OrigAccountKey) REFERENCES dim.DimAccount(AccountKey),
    CONSTRAINT FK_FactTransaction_DestAccount FOREIGN KEY (DestAccountKey) REFERENCES dim.DimAccount(AccountKey),
    CONSTRAINT FK_FactTransaction_AmountBand FOREIGN KEY (AmountBandKey) REFERENCES dim.DimAmountBand(AmountBandKey);
GO

ALTER TABLE fact.FactModelScore
ADD CONSTRAINT FK_FactModelScore_FactTransaction FOREIGN KEY (TransactionKey) REFERENCES fact.FactTransaction(TransactionKey),
    CONSTRAINT FK_FactModelScore_DimModelVersion FOREIGN KEY (ModelVersionKey) REFERENCES dim.DimModelVersion(ModelVersionKey),
    CONSTRAINT FK_FactModelScore_DimRiskPolicy FOREIGN KEY (RiskPolicyKey) REFERENCES dim.DimRiskPolicy(RiskPolicyKey),
    CONSTRAINT FK_FactModelScore_DimDate FOREIGN KEY (DateKey) REFERENCES dim.DimDate(DateKey);
GO

ALTER TABLE fact.FactAlert
ADD CONSTRAINT FK_FactAlert_FactTransaction FOREIGN KEY (TransactionKey) REFERENCES fact.FactTransaction(TransactionKey),
    CONSTRAINT FK_FactAlert_FactModelScore FOREIGN KEY (ScoreKey) REFERENCES fact.FactModelScore(ScoreKey),
    CONSTRAINT FK_FactAlert_DimRiskPolicy FOREIGN KEY (RiskPolicyKey) REFERENCES dim.DimRiskPolicy(RiskPolicyKey),
    CONSTRAINT FK_FactAlert_DimDate FOREIGN KEY (DateKey) REFERENCES dim.DimDate(DateKey);
GO

CREATE INDEX IX_FactTransaction_DateType ON fact.FactTransaction(DateKey, TransactionTypeKey);
CREATE INDEX IX_FactTransaction_Fraud ON fact.FactTransaction(IsFraud, DateKey);
CREATE INDEX IX_FactModelScore_Transaction ON fact.FactModelScore(TransactionKey, ModelVersionKey);
CREATE INDEX IX_FactAlert_LevelStatus ON fact.FactAlert(AlertLevel, AlertStatus, DateKey);
GO
