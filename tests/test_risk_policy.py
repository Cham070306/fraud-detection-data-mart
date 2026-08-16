import pytest
from src.scoring.alert_engine import classify_risk


POLICY = {"levels": {
    "low": {"min_score": 0, "max_score": .3, "alert": False, "action": "none"},
    "medium": {"min_score": .3, "max_score": .6, "alert": False, "action": "monitor"},
    "high": {"min_score": .6, "max_score": .85, "alert": True, "action": "review"},
    "critical": {"min_score": .85, "max_score": 1.000001, "alert": True, "action": "investigate"},
}}


@pytest.mark.parametrize("score,level,alert", [(0,"LOW",False),(.3,"MEDIUM",False),(.6,"HIGH",True),(.85,"CRITICAL",True),(1,"CRITICAL",True)])
def test_boundaries(score, level, alert):
    actual = classify_risk(score, POLICY)
    assert actual[:2] == (level, alert)


@pytest.mark.parametrize("score", [-.01, 1.01])
def test_rejects_invalid_score(score):
    with pytest.raises(ValueError):
        classify_risk(score, POLICY)

