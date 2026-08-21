import csv
from pathlib import Path

from scripts.build_bi_handoff import build_handoff


def _rows(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_bi_handoff_matches_registered_model_and_policy(tmp_path):
    outputs = build_handoff(
        Path("models/fraud_model_v1.0.0_metadata.json"),
        Path("configs/risk_policy.yaml"),
        tmp_path,
    )
    performance, confusion, policy = map(_rows, outputs)
    assert {row["DatasetSplit"] for row in performance} == {"VALIDATION", "TEST"}
    assert {row["ModelVersion"] for row in performance} == {"1.0.0"}
    assert sum(int(row["Count"]) for row in confusion) == 89_466
    assert [row["RiskLevel"] for row in policy] == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert [row["CreateAlert"] for row in policy] == ["False", "False", "True", "True"]
