# ML to SQL Server handoff

## FactModelScore candidate

Source file: `output/model_scoring_full_v1.0.0.csv`.

Natural key: `(TransactionKey, ModelVersion)`. The database must enforce this with a unique constraint or index. Re-running the same model must update/ignore the existing pair rather than insert a duplicate.

Required fields: `TransactionKey`, `FraudScore`, `PredictedFraud`, `RiskLevel`, `ModelVersion`, `PolicyVersion`, `ScoredAt`. The CSV also carries dashboard-friendly `DateKey`, `TimeKey`, `TransactionType` and `Amount`.

## FactAlert candidate

Source file: `output/fact_alert_v1.0.0.csv`.

Natural key: `(TransactionKey, ModelVersion)`. Only HIGH and CRITICAL policy levels are included. Initial `AlertStatus` is `NEW`.

Required fields: `TransactionKey`, `FraudScore`, `RiskLevel`, `AlertLevel`, `AlertStatus`, `RecommendedAction`, `ModelVersion`, `PolicyVersion`, `ScoredAt`.

## Required confirmation from Data Engineer

Before writing to SQL Server, confirm the database/server, authentication method, actual schema/table names, `TransactionKey` datatype and FK, batch identifier, timestamp datatypes, and whether the load contract is `MERGE`, stored procedure, or staging-table promotion. Credentials must remain in a local `.env`, never in Git.

## Idempotency validation

After load, assert that both target tables contain no duplicate `(TransactionKey, ModelVersion)` pairs and that counts reconcile with the source batch. For v1.0.0, the full score candidate contains 6,362,620 rows and the alert candidate contains 8,218 rows.
