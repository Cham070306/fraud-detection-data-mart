from pathlib import Path


_SQL = Path(__file__).parents[1] / "sql" / "10_create_dashboard_objects.sql"


def _sql_text() -> str:
    return _SQL.read_text(encoding="utf-8")


def test_dashboard_sql_has_feedback_columns():
    sql = _sql_text()
    for col in ("AnalystDecision", "FeedbackComment", "ReviewedBy", "ReviewedAt"):
        assert f"ADD\n        {col}" in sql or f"ADD\n        {col} " in sql


def test_alert_status_constraint_includes_new():
    sql = _sql_text()
    assert "'NEW'" in sql


def test_alert_status_constraint_keeps_existing_values():
    sql = _sql_text()
    for value in ("'OPEN'", "'IN_REVIEW'", "'RESOLVED'", "'FALSE_POSITIVE'"):
        assert value in sql


def test_decision_check_values_present():
    sql = _sql_text()
    for value in ("'CONFIRMED_FRAUD'", "'FALSE_POSITIVE'", "'UNDER_INVESTIGATION'"):
        assert value in sql


def test_dashboard_views_created():
    sql = _sql_text()
    for view in (
        "vw_AlertQueue",
        "vw_TransactionAnalysis",
        "vw_AlertFeedback",
        "vw_ETLQualitySummary",
    ):
        assert f"CREATE OR ALTER VIEW bi.{view}" in sql


def test_reconciliation_rate_computed():
    sql = _sql_text()
    assert "ReconciliationRate" in sql
    assert "NULLIF(r.ExpectedSourceRows" in sql
