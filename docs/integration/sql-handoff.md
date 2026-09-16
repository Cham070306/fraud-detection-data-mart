# ML to SQL Server handoff

Power BI contract, reference tables and acceptance checks are documented in
`docs/integration/bi-model-handoff.md`.

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

## Handoff boundary

TV4 owns the feature list, model/threshold metadata, scoring fields, policy
mapping and ML reconciliation totals. TV2 owns the physical SQL load, keys,
constraints, batch transaction and database reconciliation. TV5 consumes only
the agreed BI views after TV2 and TV4 sign off the row counts and versions.

## Implemented load path

Production scoring now reads `TransactionKey`, `DateKey` and `TimeKey` directly
from SQL Server, avoiding row-number joins with the raw CSV:

```powershell
.\scripts\score_transactions.ps1 -FromSql
.\scripts\load_ml_results.ps1
python scripts/run_validation.py --require-ml
```

The loader upserts model metadata and risk policy, merges scores on
`(TransactionKey, ModelVersionKey)`, creates alerts from HIGH/CRITICAL rows and
preserves existing analyst feedback. SQL migration 11 adds the unique indexes
required for safe re-runs. Runtime sign-off still requires executing the commands
against the target SQL Server and reconciling 6.362.620 scores and 8.218 alerts.
