# PaySim Fraud Detection - Model Report v1.0.0

## Scope and data

- Source: PaySim CSV, 6,362,620 simulated transactions.
- Target: `isFraud` (8,213 positive transactions overall).
- Intended use: prioritize simulated transactions for review; not approved for real banking production.

## Chronological split

| Set | Step range | Rows | Fraud rows | Use |
|---|---:|---:|---:|---|
| Train | 1-520 | 6,082,007 | 5,781 | Fit preprocessing/models |
| Validation | 521-631 | 191,147 | 1,180 | Compare models and select threshold |
| Test | 632-743 | 89,466 | 1,252 | One final evaluation |

Preprocessing was fit on train only. The target, identifiers, downstream score/risk/alert fields and `isFlaggedFraud` were excluded from X.

## Models and validation results

| Model | Training rows | PR-AUC | Precision | Recall | F2 | FP | FN | Alerts | Fraud amount captured | Fraud amount missed | Capture rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Business rule (`baseline_rule`) | 6,082,007 | 0.024149 | 0.030893 | 0.981356 | 0.137191 | 36,326 | 22 | 37,484 | 1,330,804,126.27 | 166,472,835.47 | 88.8816% |
| Logistic Regression | 6,082,007 | 0.846412 | 0.640127 | 0.851695 | 0.798887 | 565 | 175 | 1,570 | 1,473,381,337.37 | 23,895,624.37 | 98.4041% |
| Random Forest | 500,000 | 0.999997 | 0.996622 | 1.000000 | 0.999322 | 4 | 0 | 1,184 | 1,497,276,961.73 | 0.00 | 100.0000% |

Random Forest was selected. To keep tree training tractable, its fit set retained every fraud row and sampled non-fraud rows up to 500,000 total rows. Model comparison and threshold selection used the complete validation set.

## Threshold and final test

- Selected validation threshold: **0.32**.
- Test PR-AUC: **0.999999**.
- Test precision: **0.999201**.
- Test recall: **0.999201**.
- Test F2: **0.999201**.
- Confusion matrix: TN 88,213; FP 1; FN 1; TP 1,251.
- Test alerts at model threshold: 1,252 (13.994 per 1,000 transactions).
- Test fraud amount captured: **2,129,729,633.40**.
- Test fraud amount missed: **399,045.09**.
- Test fraud amount capture rate: **99.981267%**.

The threshold is a technical recommendation selected by validation F2 subject to minimum recall. It is not yet business-approved. Final approval requires confirmed FP/FN costs, daily alert-review capacity and sign-off from the risk-policy owner.

## Evaluation artifacts

- [Threshold analysis](../../output/evaluation/threshold_analysis.csv)
- [Model comparison](../../output/evaluation/model_comparison.csv)
- [Test confusion matrix](../../output/evaluation/confusion_matrix_test.svg)
- [Validation precision-recall curve](../../output/evaluation/precision_recall_validation.svg)
- [Threshold metrics](../../output/evaluation/threshold_metrics.svg)
- [Threshold alert volume](../../output/evaluation/threshold_alert_volume.svg)

## Full scoring output

- Scored rows: 6,362,620.
- Model version / policy version: 1.0.0 / 1.0.0.
- Score range: 0.0-1.0.
- Risk distribution: LOW 6,354,165; MEDIUM 237; HIGH 46; CRITICAL 8,172.
- HIGH + CRITICAL alerts: 8,218.
- Predicted fraud at model threshold: 8,401.
- Transaction keys are contiguous and unique in the generated CSV.

## Limitations

PaySim is synthetic and the balance-derived variables make its fraud patterns unusually separable. The near-perfect metrics must not be treated as evidence of production banking performance. Before operational use, validate temporal stability, probability calibration, alert capacity, data drift and performance on representative real-world data.

SQL Server loading is not complete: `FactModelScore`, `FactAlert`, SQL idempotency, foreign keys, batch controls and database row-count reconciliation remain dependent on Data Engineer connection/schema details. Git provenance is also unavailable for this working directory, so metadata intentionally records `git_commit: null`.
