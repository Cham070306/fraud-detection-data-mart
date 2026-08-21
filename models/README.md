# Model artifacts

Training writes a versioned `.joblib`, metadata JSON and feature-list JSON here.
Large model binaries are intentionally ignored by Git.

To reproduce the Power BI reference tables from the registered metadata and
risk policy, run `python scripts/build_bi_handoff.py`. See
`docs/integration/bi-model-handoff.md` for the handoff contract.
