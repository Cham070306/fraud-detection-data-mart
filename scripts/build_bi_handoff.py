"""Build small, versioned ML reference tables for the Power BI handoff."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"No rows supplied for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_handoff(metadata_path: Path, policy_path: Path, output_dir: Path) -> list[Path]:
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    policy = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    version = str(metadata["version"])

    performance_rows = []
    for split_name, key in (("VALIDATION", "validation_metrics"), ("TEST", "test_metrics")):
        metrics = metadata[key]
        performance_rows.append({
            "ModelVersion": version,
            "ModelName": metadata["model_name"],
            "DatasetSplit": split_name,
            "Threshold": metadata["threshold"],
            "PRAUC": metrics["pr_auc"],
            "Precision": metrics["precision"],
            "Recall": metrics["recall"],
            "F2": metrics["f2"],
            "Alerts": metrics["alert_count"],
            "AlertsPer1000": metrics["alerts_per_1000"],
            "FraudAmountCaptured": metrics.get("fraud_amount_captured", ""),
            "FraudAmountMissed": metrics.get("fraud_amount_missed", ""),
            "FraudAmountCaptureRate": metrics.get("fraud_amount_capture_rate", ""),
        })

    test = metadata["test_metrics"]
    confusion_rows = [
        {"ModelVersion": version, "ActualClass": "LEGIT", "PredictedClass": "LEGIT", "Count": test["tn"]},
        {"ModelVersion": version, "ActualClass": "LEGIT", "PredictedClass": "FRAUD", "Count": test["fp"]},
        {"ModelVersion": version, "ActualClass": "FRAUD", "PredictedClass": "LEGIT", "Count": test["fn"]},
        {"ModelVersion": version, "ActualClass": "FRAUD", "PredictedClass": "FRAUD", "Count": test["tp"]},
    ]

    policy_rows = []
    for item in policy["risk_levels"]:
        policy_rows.append({
            "PolicyVersion": policy["policy_version"],
            "RiskLevel": item["level"],
            "ScoreMin": item["score_min"],
            "ScoreMax": item["score_max"],
            "RecommendedAction": item["action"],
            "CreateAlert": item["generate_alert"],
            "Priority": item["priority"],
        })

    outputs = [
        output_dir / "model_performance.csv",
        output_dir / "confusion_matrix.csv",
        output_dir / "risk_policy.csv",
    ]
    _write_csv(outputs[0], performance_rows)
    _write_csv(outputs[1], confusion_rows)
    _write_csv(outputs[2], policy_rows)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", default="models/fraud_model_v1.0.0_metadata.json")
    parser.add_argument("--policy", default="configs/risk_policy.yaml")
    parser.add_argument("--output-dir", default="docs/integration/bi_model_handoff")
    args = parser.parse_args()
    outputs = build_handoff(Path(args.metadata), Path(args.policy), Path(args.output_dir))
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
