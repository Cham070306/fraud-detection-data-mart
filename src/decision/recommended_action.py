def recommended_action(risk_level: str) -> str:
    actions = {
        "LOW": "No action", "MEDIUM": "Monitor transaction",
        "HIGH": "Review within 24 hours", "CRITICAL": "Immediate investigation",
    }
    try:
        return actions[risk_level.upper()]
    except KeyError as exc:
        raise ValueError(f"Unknown RiskLevel: {risk_level}") from exc
