/* =============================================================
   07_seed_dimensions.sql
   Seed du lieu cho cac dimension
   ============================================================= */

USE FraudDW;
GO

-- DimDate: 31 ngay mo phong, map tu 2023-01-01
INSERT INTO dim.DimDate (DateKey, StepDay, DayOfWeek, DayOfWeekNum, WeekOfSimulation, IsWeekend)
SELECT
    CONVERT(INT, CONVERT(CHAR(8), DATEADD(DAY, v.n - 1, '2023-01-01'), 112)) AS DateKey,
    v.n AS StepDay,
    DATENAME(WEEKDAY, DATEADD(DAY, v.n - 1, '2023-01-01')) AS DayOfWeek,
    DATEPART(WEEKDAY, DATEADD(DAY, v.n - 1, '2023-01-01')) AS DayOfWeekNum,
    ((v.n - 1) / 7) + 1 AS WeekOfSimulation,
    CASE WHEN DATEPART(WEEKDAY, DATEADD(DAY, v.n - 1, '2023-01-01')) IN (1,7) THEN 1 ELSE 0 END AS IsWeekend
FROM (VALUES
(1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12),(13),(14),(15),(16),(17),(18),(19),(20),(21),(22),(23),(24),(25),(26),(27),(28),(29),(30),(31)
) v(n)
WHERE NOT EXISTS (SELECT 1 FROM dim.DimDate d WHERE d.StepDay = v.n);
GO

INSERT INTO dim.DimTime (TimeKey, HourOfDay, TimeSlot, IsPeakHour)
SELECT * FROM (VALUES
(0,0,'NIGHT',0),(1,1,'NIGHT',0),(2,2,'NIGHT',0),(3,3,'NIGHT',0),(4,4,'NIGHT',0),(5,5,'NIGHT',0),
(6,6,'MORNING',0),(7,7,'MORNING',0),(8,8,'MORNING',1),(9,9,'MORNING',1),(10,10,'MORNING',1),(11,11,'MORNING',1),
(12,12,'AFTERNOON',1),(13,13,'AFTERNOON',1),(14,14,'AFTERNOON',1),(15,15,'AFTERNOON',1),(16,16,'AFTERNOON',1),(17,17,'AFTERNOON',1),
(18,18,'EVENING',0),(19,19,'EVENING',0),(20,20,'EVENING',0),(21,21,'EVENING',0),
(22,22,'LATE_NIGHT',0),(23,23,'LATE_NIGHT',0)
) AS x(TimeKey, HourOfDay, TimeSlot, IsPeakHour)
WHERE NOT EXISTS (SELECT 1 FROM dim.DimTime t WHERE t.TimeKey = x.TimeKey);
GO

INSERT INTO dim.DimTransactionType (TransactionTypeKey, TypeCode, TypeName, IsHighRiskType, Description)
SELECT * FROM (VALUES
(1,'CASH_IN',N'Nộp tiền',0,N'Giao dịch nộp tiền vào tài khoản'),
(2,'CASH_OUT',N'Rút tiền',1,N'Rút tiền ra khỏi tài khoản'),
(3,'DEBIT',N'Trừ tiền',0,N'Giao dịch trừ tiền nội bộ'),
(4,'PAYMENT',N'Thanh toán',0,N'Thanh toán hàng hóa/dịch vụ'),
(5,'TRANSFER',N'Chuyển tiền',1,N'Chuyển tiền giữa hai tài khoản')
) AS x(TransactionTypeKey, TypeCode, TypeName, IsHighRiskType, Description)
WHERE NOT EXISTS (SELECT 1 FROM dim.DimTransactionType t WHERE t.TypeCode = x.TypeCode);
GO

INSERT INTO dim.DimAccount (AccountKey, AccountID, AccountType)
SELECT 0, 'UNKNOWN', 'C'
WHERE NOT EXISTS (SELECT 1 FROM dim.DimAccount WHERE AccountKey = 0);
GO

INSERT INTO dim.DimAmountBand (AmountBandKey, BandCode, BandLabel, LowerBound, UpperBound, RiskWeight)
SELECT * FROM (VALUES
(1,'XS',N'Rất nhỏ',0,1000,1.0),
(2,'S',N'Nhỏ',1000,10000,1.0),
(3,'M',N'Trung bình',10000,100000,1.0),
(4,'L',N'Lớn',100000,1000000,1.0),
(5,'XL',N'Rất lớn',1000000,10000000,1.0),
(6,'XXL',N'Cực lớn',10000000,NULL,1.0)
) AS x(AmountBandKey, BandCode, BandLabel, LowerBound, UpperBound, RiskWeight)
WHERE NOT EXISTS (SELECT 1 FROM dim.DimAmountBand b WHERE b.BandCode = x.BandCode);
GO

INSERT INTO dim.DimRiskPolicy (RiskPolicyKey, PolicyVersion, RiskLevel, ScoreThresholdMin, ScoreThresholdMax, RecommendedAction, EffectiveDate, IsActive)
SELECT * FROM (VALUES
(1,'v1.0','LOW',0.0000,0.3000,'ALLOW','2026-08-09',1),
(2,'v1.0','MEDIUM',0.3000,0.6000,'STEP_UP_VERIFY','2026-08-09',1),
(3,'v1.0','HIGH',0.6000,0.8500,'HOLD_AND_REVIEW','2026-08-09',1),
(4,'v1.0','CRITICAL',0.8500,1.0000,'BLOCK_AND_ALERT','2026-08-09',1)
) AS x(RiskPolicyKey, PolicyVersion, RiskLevel, ScoreThresholdMin, ScoreThresholdMax, RecommendedAction, EffectiveDate, IsActive)
WHERE NOT EXISTS (SELECT 1 FROM dim.DimRiskPolicy p WHERE p.PolicyVersion = x.PolicyVersion AND p.RiskLevel = x.RiskLevel);
GO

INSERT INTO dim.DimModelVersion (ModelVersionKey, ModelName, Version, IsProduction)
SELECT 1, 'LightGBM', 'v1.0', 1
WHERE NOT EXISTS (SELECT 1 FROM dim.DimModelVersion WHERE ModelVersionKey = 1);
GO
