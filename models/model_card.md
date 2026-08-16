# PaySim Fraud Model Card

- Status: active candidate, version 1.0.0
- Owner: ML Engineer (TV4)
- Intended use: rank simulated PaySim transactions for fraud review.
- Not intended for: real banking production decisions or automatic customer blocking.
- Split: chronological by `step`; threshold selected on validation only.
- Leakage controls: target, identifiers, downstream score/risk/alert fields, and `isFlaggedFraud` are excluded.
- Required metrics: PR-AUC, precision, recall, F2, FP, FN and alert volume.
- Limitations: PaySim is synthetic; probabilities require calibration and validation on representative data.
- Rollback: retain the previous versioned artifact, metadata, feature list and risk policy.

## Registered result

- Selected algorithm: Random Forest; tree fit capped at 500,000 rows while retaining every train fraud row.
- Chronological split: train steps 1-520, validation 521-631, test 632-743.
- Threshold: 0.32, selected on validation.
- Test: PR-AUC 0.999999; precision/recall/F2 0.999201; FP 1; FN 1.
- Integrity: model SHA-256 is stored in `models/registry.json` and checked when resolving a registered model.
