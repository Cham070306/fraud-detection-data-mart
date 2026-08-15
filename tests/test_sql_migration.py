from pathlib import Path


def test_idempotency_migration_stops_before_index_when_duplicates_exist():
    sql = (Path(__file__).parents[1] / "sql" / "09_etl_idempotency_migration.sql").read_text(
        encoding="utf-8"
    )
    assert "HAVING COUNT_BIG(*) > 1" in sql
    assert "THROW 51000" in sql
    assert sql.index("THROW 51000") < sql.index("CREATE UNIQUE INDEX")
    assert "DELETE" not in sql.upper()
