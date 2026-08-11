/* =============================================================
   04_create_fact_tables.sql
   3 bang fact: FactTransaction, FactModelScore, FactAlert
   ============================================================= */

USE FraudDW;
GO

IF OBJECT_ID(N'fact.FactTransaction', N'U') IS NOT NULL DROP TABLE fact.FactTransaction;
GO
CREATE TABLE fact.FactTransaction (
    TransactionKey      BIGINT          IDENTITY(1,1) NOT NULL,
    DateKey             INT             NOT NULL,
    TimeKey             INT             NOT NULL,
    TransactionTypeKey  INT             NOT NULL,
    OrigAccountKey      INT             NOT NULL,
    DestAccountKey      INT             NOT NULL,
    AmountBandKey       INT             NOT NULL,
    StepRaw             INT             NOT NULL,
    Amount              DECIMAL(18,2)   NOT NULL,
    OldBalanceOrig      DECIMAL(18,2)   NOT NULL,
    NewBalanceOrig      DECIMAL(18,2)   NOT NULL,
    OldBalanceDest      DECIMAL(18,2)   NOT NULL,
    NewBalanceDest      DECIMAL(18,2)   NOT NULL,
    IsFraud             BIT             NOT NULL,
    IsFlaggedFraud      BIT             NOT NULL,
    BalanceDropOrig     AS (OldBalanceOrig - NewBalanceOrig) PERSISTED,
    LoadedAt            DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_FactTransaction PRIMARY KEY CLUSTERED (TransactionKey)
);
GO

IF OBJECT_ID(N'fact.FactModelScore', N'U') IS NOT NULL DROP TABLE fact.FactModelScore;
GO
CREATE TABLE fact.FactModelScore (
    ScoreKey            BIGINT          IDENTITY(1,1) NOT NULL,
    TransactionKey      BIGINT          NOT NULL,
    ModelVersionKey     INT             NOT NULL,
    RiskPolicyKey       INT             NOT NULL,
    DateKey             INT             NOT NULL,
    FraudScore          DECIMAL(7,6)    NOT NULL,
    RiskLevel           VARCHAR(10)     NOT NULL,
    RecommendedAction   VARCHAR(30)     NOT NULL,
    IsPredictedFraud    BIT             NOT NULL,
    ScoredAt            DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_FactModelScore PRIMARY KEY CLUSTERED (ScoreKey)
);
GO

IF OBJECT_ID(N'fact.FactAlert', N'U') IS NOT NULL DROP TABLE fact.FactAlert;
GO
CREATE TABLE fact.FactAlert (
    AlertKey            BIGINT          IDENTITY(1,1) NOT NULL,
    TransactionKey      BIGINT          NOT NULL,
    ScoreKey            BIGINT          NOT NULL,
    RiskPolicyKey       INT             NOT NULL,
    DateKey             INT             NOT NULL,
    AlertLevel          VARCHAR(10)     NOT NULL,
    AlertStatus         VARCHAR(15)     NOT NULL,
    FraudScore          DECIMAL(7,6)    NOT NULL,
    AlertAmount         DECIMAL(18,2)   NOT NULL,
    CreatedAt           DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    ResolvedAt          DATETIME2       NULL,
    CONSTRAINT PK_FactAlert PRIMARY KEY CLUSTERED (AlertKey),
    CONSTRAINT CK_FactAlert_Level CHECK (AlertLevel IN ('HIGH','CRITICAL')),
    CONSTRAINT CK_FactAlert_Status CHECK (AlertStatus IN ('OPEN','IN_REVIEW','RESOLVED','FALSE_POSITIVE'))
);
GO
