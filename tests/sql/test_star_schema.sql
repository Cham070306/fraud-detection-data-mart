-- Basic star schema smoke test
SELECT COUNT(*) AS Cnt FROM dim.DimDate;
SELECT COUNT(*) AS Cnt FROM dim.DimTime;
SELECT COUNT(*) AS Cnt FROM dim.DimTransactionType;
SELECT COUNT(*) AS Cnt FROM dim.DimAccount;
SELECT COUNT(*) AS Cnt FROM dim.DimAmountBand;
SELECT COUNT(*) AS Cnt FROM dim.DimRiskPolicy;
SELECT COUNT(*) AS Cnt FROM dim.DimModelVersion;
