#!/usr/bin/env python
"""Create or migrate FraudDW with fail-fast SQL batch execution."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import AppConfig


SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
BASE_FILES = [
    "01_create_schemas.sql",
    "02_create_staging_tables.sql",
    "03_create_dimensions.sql",
    "04_create_fact_tables.sql",
    "05_create_constraints_indexes.sql",
    "06_create_bi_views.sql",
    "07_seed_dimensions.sql",
    "10_create_dashboard_objects.sql",
    "11_ml_integration_migration.sql",
]
MIGRATION_FILES = [
    "09_etl_idempotency_migration.sql",
    "10_create_dashboard_objects.sql",
    "11_ml_integration_migration.sql",
]


def connection_string(db_cfg, database: str) -> str:
    if db_cfg.username and db_cfg.password:
        auth = f"UID={db_cfg.username};PWD={db_cfg.password};"
    elif db_cfg.trusted_connection:
        auth = "Trusted_Connection=yes;"
    else:
        auth = ""
    return (
        f"DRIVER={{{db_cfg.driver}}};SERVER={db_cfg.server};DATABASE={database};"
        f"{auth}TrustServerCertificate=yes"
    )


def sql_batches(path: Path):
    content = path.read_text(encoding="utf-8-sig")
    return [part.strip() for part in re.split(r"(?im)^\s*GO\s*(?:--.*)?$", content) if part.strip()]


def execute_file(conn, path: Path) -> None:
    cur = conn.cursor()
    try:
        for batch_number, batch in enumerate(sql_batches(path), start=1):
            try:
                cur.execute(batch)
                while cur.nextset():
                    pass
            except Exception as exc:
                conn.rollback()
                raise RuntimeError(f"{path.name}, batch {batch_number}: {exc}") from exc
        conn.commit()
        print(f"[OK] {path.name}")
    finally:
        cur.close()


def has_core_tables(conn) -> bool:
    cur = conn.cursor()
    try:
        cur.execute("SELECT CASE WHEN OBJECT_ID(N'fact.FactTransaction', N'U') IS NULL THEN 0 ELSE 1 END")
        return bool(cur.fetchone()[0])
    finally:
        cur.close()


def main():
    parser = argparse.ArgumentParser(description="Create or migrate FraudDW")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--rebuild", action="store_true",
        help="Drop and recreate project tables. This removes existing DW data.",
    )
    mode.add_argument(
        "--migrate", action="store_true",
        help="Run only non-destructive migrations on an existing database.",
    )
    args = parser.parse_args()

    cfg = AppConfig.load()
    if cfg.db.database.lower() != "frauddw":
        parser.error("SQL files target FraudDW; set FRAUD_DB_NAME=FraudDW")

    import pyodbc

    master = pyodbc.connect(connection_string(cfg.db, "master"), autocommit=True)
    try:
        execute_file(master, SQL_DIR / "00_create_database.sql")
    finally:
        master.close()

    conn = pyodbc.connect(connection_string(cfg.db, cfg.db.database), autocommit=False)
    try:
        existing = has_core_tables(conn)
        if args.migrate and not existing:
            parser.error("--migrate requires an initialized FraudDW database")
        if args.migrate or (existing and not args.rebuild):
            files = MIGRATION_FILES
            print("Existing database detected; applying non-destructive migrations.")
        else:
            files = BASE_FILES
            if args.rebuild and existing:
                print("Rebuild requested; existing project tables will be recreated.")
                execute_file(conn, SQL_DIR / "00_reset_project_objects.sql")
        for name in files:
            execute_file(conn, SQL_DIR / name)

        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.name, COUNT(o.object_id)
            FROM sys.schemas AS s
            LEFT JOIN sys.objects AS o ON o.schema_id = s.schema_id
            WHERE s.name IN ('stg','dim','fact','audit','bi')
            GROUP BY s.name ORDER BY s.name
            """
        )
        print("Schema object counts:")
        for schema_name, count in cur.fetchall():
            print(f"  {schema_name}: {count}")
        cur.close()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
