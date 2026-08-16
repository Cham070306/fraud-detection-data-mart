"""Public decision-layer facade for the versioned risk policy."""
from src.scoring.alert_engine import classify_risk, load_policy

__all__ = ["classify_risk", "load_policy"]
