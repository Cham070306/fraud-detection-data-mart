/* =============================================================
   03_create_dimensions.sql
   7 bang dimension: DimDate, DimTime, DimTransactionType,
   DimAccount, DimAmountBand, DimRiskPolicy, DimModelVersion
   ============================================================= */

USE FraudDW;
GO

-- 1. DimDate
IF OBJECT_ID(N'dim.DimDate', N'U') IS NOT NULL DROP TABLE dim.DimDate;
GO

CREATE TABLE dim.DimDate (
    DateKey             INT             NOT NULL,   -- YYYYMMDD
    StepDay             INT             NOT NULL,   -- 1..31
    DayOfWeek           VARCHAR(10)     NOT NULL,
    DayOfWeekNum        INT             NOT NULL,   -- 1=Mon, 7=Sun
    WeekOfSimulation    INT             NOT NULL,   -- 1..5
    IsWeekend           BIT             NOT NULL,
    CONSTRAINT PK_DimDate PRIMARY KEY CLUSTERED (DateKey),
    CONSTRAINT UQ_DimDate_StepDay UNIQUE (StepDay)
);
GO

-- 2. DimTime
IF OBJECT_ID(N'dim.DimTime', N'U') IS NOT NULL DROP TABLE dim.DimTime;
GO

CREATE TABLE dim.DimTime (
    TimeKey             INT             NOT NULL,   -- 0..23
    HourOfDay           INT             NOT NULL,
    TimeSlot            VARCHAR(20)     NOT NULL,   -- LATE_NIGHT/NIGHT/MORNING/AFTERNOON/EVENING
    IsPeakHour          BIT             NOT NULL,
    CONSTRAINT PK_DimTime PRIMARY KEY CLUSTERED (TimeKey),
    CONSTRAINT CK_DimTime_Hour CHECK (HourOfDay BETWEEN 0 AND 23),
    CONSTRAINT CK_DimTime_Slot CHECK (TimeSlot IN ('LATE_NIGHT','NIGHT','MORNING','AFTERNOON','EVENING'))
);
GO

-- 3. DimTransactionType
IF OBJECT_ID(N'dim.DimTransactionType', N'U') IS NOT NULL DROP TABLE dim.DimTransactionType;
GO

CREATE TABLE dim.DimTransactionType (
    TransactionTypeKey  INT             NOT NULL,
    TypeCode            VARCHAR(10)     NOT NULL,
    TypeName            NVARCHAR(50)    NOT NULL,
    IsHighRiskType      BIT             NOT NULL,
    Description         NVARCHAR(200)   NULL,
    CONSTRAINT PK_DimTransactionType PRIMARY KEY CLUSTERED (TransactionTypeKey),
    CONSTRAINT UQ_DimTransactionType_Code UNIQUE (TypeCode)
);
GO

-- 4. DimAccount
IF OBJECT_ID(N'dim.DimAccount', N'U') IS NOT NULL DROP TABLE dim.DimAccount;
GO

CREATE TABLE dim.DimAccount (
    AccountKey          INT             NOT NULL,
    AccountID           VARCHAR(20)     NOT NULL,
    AccountType         CHAR(1)         NOT NULL,   -- C=Customer, M=Merchant
    CONSTRAINT PK_DimAccount PRIMARY KEY CLUSTERED (AccountKey),
    CONSTRAINT UQ_DimAccount_ID UNIQUE (AccountID),
    CONSTRAINT CK_DimAccount_Type CHECK (AccountType IN ('C','M'))
);
GO

-- 5. DimAmountBand
IF OBJECT_ID(N'dim.DimAmountBand', N'U') IS NOT NULL DROP TABLE dim.DimAmountBand;
GO

CREATE TABLE dim.DimAmountBand (
    AmountBandKey       INT             NOT NULL,
    BandCode            VARCHAR(10)     NOT NULL,
    BandLabel           NVARCHAR(50)    NOT NULL,
    LowerBound          DECIMAL(18,2)   NOT NULL,
    UpperBound          DECIMAL(18,2)   NULL,       -- NULL cho XXL
    RiskWeight          DECIMAL(5,2)    NOT NULL DEFAULT 1.0,
    CONSTRAINT PK_DimAmountBand PRIMARY KEY CLUSTERED (AmountBandKey),
    CONSTRAINT UQ_DimAmountBand_Code UNIQUE (BandCode)
);
GO

-- 6. DimRiskPolicy
IF OBJECT_ID(N'dim.DimRiskPolicy', N'U') IS NOT NULL DROP TABLE dim.DimRiskPolicy;
GO

CREATE TABLE dim.DimRiskPolicy (
    RiskPolicyKey       INT             NOT NULL,
    PolicyVersion       VARCHAR(10)     NOT NULL,
    RiskLevel           VARCHAR(10)     NOT NULL,
    ScoreThresholdMin   DECIMAL(5,4)    NOT NULL,
    ScoreThresholdMax   DECIMAL(5,4)    NOT NULL,
    RecommendedAction   VARCHAR(30)     NOT NULL,
    EffectiveDate       DATE            NOT NULL,
    IsActive            BIT             NOT NULL DEFAULT 1,
    CONSTRAINT PK_DimRiskPolicy PRIMARY KEY CLUSTERED (RiskPolicyKey),
    CONSTRAINT CK_DimRiskPolicy_Level CHECK (RiskLevel IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    CONSTRAINT CK_DimRiskPolicy_Action CHECK (RecommendedAction IN ('ALLOW','STEP_UP_VERIFY','HOLD_AND_REVIEW','BLOCK_AND_ALERT'))
);
GO

-- 7. DimModelVersion
IF OBJECT_ID(N'dim.DimModelVersion', N'U') IS NOT NULL DROP TABLE dim.DimModelVersion;
GO

CREATE TABLE dim.DimModelVersion (
    ModelVersionKey     INT             NOT NULL,
    ModelName           VARCHAR(50)     NOT NULL,
    Version             VARCHAR(10)     NOT NULL,
    TrainDate           DATE            NULL,
    Precision           DECIMAL(5,4)    NULL,
    Recall              DECIMAL(5,4)    NULL,
    F2Score             DECIMAL(5,4)    NULL,
    PrAUC               DECIMAL(5,4)    NULL,
    Threshold           DECIMAL(5,4)    NULL,
    IsProduction        BIT             NOT NULL DEFAULT 0,
    ModelFilePath       NVARCHAR(500)   NULL,
    CONSTRAINT PK_DimModelVersion PRIMARY KEY CLUSTERED (ModelVersionKey),
    CONSTRAINT UQ_DimModelVersion_NameVer UNIQUE (ModelName, Version)
);
GO

PRINT 'Da tao 7 bang dimension';
GO
