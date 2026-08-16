# PaySim Fraud Detection ML

Leakage-safe feature, training, threshold-selection, scoring and alert pipeline for the TV4 scope of the PaySim Fraud Data Mart.

## Setup

```powershell
python -m venv .venv-ml
.\.venv-ml\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "."
```

Keep the 493 MB PaySim CSV outside Git (or under `data/raw/`).

## Test

```powershell
python -m pytest tests/test_ml_pipeline.py tests/test_risk_policy.py -v
```

## Train and score

```powershell
python scripts/train_model.py --input "..\PS_20174392719_1491204439457_log.csv" --output-dir models --version 1.0.0
python scripts/score_transactions.py --input "..\PS_20174392719_1491204439457_log.csv" --model models/fraud_model_v1.0.0.joblib --metadata models/fraud_model_v1.0.0_metadata.json --output output/model_scoring_sample.csv --rows 10000
```

PowerShell wrappers are also available:

```powershell
.\scripts\train_model.ps1 -InputCsv "..\PS_20174392719_1491204439457_log.csv" -Version "1.0.0"
.\scripts\score_transactions.ps1 -InputCsv "..\PS_20174392719_1491204439457_log.csv" -Version "1.0.0"
```

Official evaluation artifacts are under `output/evaluation/`. SQL handoff fields and idempotency requirements are documented in `docs/integration/sql-handoff.md`.

For a quick development run, add `--rows 200000` to training. Do not use that limited run as final reported evidence.
