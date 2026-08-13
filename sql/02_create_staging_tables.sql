/* =============================================================
   02_create_staging_tables.sql
   stg.TransactionRaw - bang luu du lieu thoc tu CSV
   ============================================================= */

USE FraudDW;
GO

IF OBJECT_ID(N'stg.TransactionRaw', N'U') IS NOT NULL DROP TABLE stg.TransactionRaw;
GO

CREATE TABLE stg.TransactionRaw (
    BatchID             INT             NOT NULL,
    SourceFileName      NVARCHAR(500)   NOT NULL,
    RowNumberInChunk    INT             NOT NULL,
    StepRaw             INT             NOT NULL,
    TypeCode            VARCHAR(10)     NOT NULL,
    Amount              DECIMAL(18,2)   NOT NULL,
    NameOrig            VARCHAR(20)     NOT NULL,
    OldBalanceOrg       DECIMAL(18,2)   NOT NULL,
    NewBalanceOrig      DECIMAL(18,2)   NOT NULL,
    NameDest            VARCHAR(20)     NOT NULL,
    OldBalanceDest      DECIMAL(18,2)   NOT NULL,
    NewBalanceDest      DECIMAL(18,2)   NOT NULL,
    IsFraud             TINYINT         NOT NULL,
    IsFlaggedFraud      TINYINT         NOT NULL,
    LoadedAt            DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_stg_TransactionRaw PRIMARY KEY CLUSTERED (BatchID, RowNumberInChunk)
);
GO

PRINT 'Da tao stg.TransactionRaw';
GO

/* ---- Audit tables (batch log, reject log, reconciliation log) ---- */

IF OBJECT_ID(N'audit.ETLBatchLog', N'U') IS NOT NULL DROP TABLE audit.ETLBatchLog;
GO
CREATE TABLE audit.ETLBatchLog (
    BatchID         INT IDENTITY(1,1) NOT NULL,
    SourceFileName  NVARCHAR(500)   NOT NULL,
    Status          VARCHAR(15)     NOT NULL,
    StartedAt       DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    FinishedAt      DATETIME2       NULL,
    Message         NVARCHAR(1000)  NULL,
    CONSTRAINT PK_ETLBatchLog PRIMARY KEY CLUSTERED (BatchID)
);
GO

IF OBJECT_ID(N'audit.RejectLog', N'U') IS NOT NULL DROP TABLE audit.RejectLog;
GO
CREATE TABLE audit.RejectLog (
    RejectID        BIGINT IDENTITY(1,1) NOT NULL,
    BatchID         INT             NOT NULL,
    SourceFileName  NVARCHAR(500)   NOT NULL,
    ChunkIndex      INT             NOT NULL,
    StepRaw         INT             NULL,
    Reason          NVARCHAR(500)   NOT NULL,
    CreatedAt       DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_RejectLog PRIMARY KEY CLUSTERED (RejectID)
);
GO

IF OBJECT_ID(N'audit.ReconciliationLog', N'U') IS NOT NULL DROP TABLE audit.ReconciliationLog;
GO
CREATE TABLE audit.ReconciliationLog (
    ReconID             BIGINT IDENTITY(1,1) NOT NULL,
    BatchID             INT             NOT NULL,
    FactRows            BIGINT          NOT NULL,
    FactAmount          DECIMAL(20,2)   NOT NULL,
    FactFraudCount      BIGINT          NOT NULL,
    ExpectedSourceRows  BIGINT          NOT NULL,
    ExpectedAmountSum   DECIMAL(20,2)   NOT NULL,
    ExpectedFraudCount  BIGINT          NOT NULL,
    Status              VARCHAR(10)     NOT NULL,
    CreatedAt           DATETIME2       NOT NULL DEFAULT SYSDATETIME(),
    CONSTRAINT PK_ReconciliationLog PRIMARY KEY CLUSTERED (ReconID)
);
GO

PRINT 'Da tao stg.TransactionRaw va 3 bang audit';
GO
