from __future__ import annotations

from pathlib import Path
import yaml


def load_policy(path):
    with Path(path).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def classify_risk(score: float, policy: dict):
    if not 0 <= float(score) <= 1:
        raise ValueError("FraudScore must be in [0, 1]")
    if policy.get("risk_levels"):
        for rule in policy["risk_levels"]:
            lower = float(rule["score_min"])
            upper = float(rule["score_max"])
            in_range = lower <= score < upper
            if rule["level"].upper() == "CRITICAL":
                in_range = lower <= score <= upper
            if in_range:
                return (
                    rule["level"].upper(),
                    bool(rule["generate_alert"]),
                    rule["action"],
                )
    for name, rule in policy["levels"].items():
        if rule["min_score"] <= score < rule["max_score"]:
            return name.upper(), bool(rule["alert"]), rule["action"]
    raise ValueError(f"No risk policy interval covers score {score}")
