from __future__ import annotations
from typing import Any
from src.common.config import AppConfig, DatabaseConfig

def get_connection(cfg: AppConfig | DatabaseConfig | None = None) -> Any:
    # Import lazily so pure unit tests with fake connections do not require the
    # host-level unixODBC driver. A real SQL Server connection still fails here
    # with the original ImportError when the driver is not installed.
    import pyodbc

    if cfg is None:
        cfg = AppConfig.load()
    if isinstance(cfg, AppConfig):
        db_cfg = cfg.db
    else:
        db_cfg = cfg
    return pyodbc.connect(db_cfg.connection_string(), autocommit=False)

def execute(conn: Any, sql: str, params: tuple = ()) -> None:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def query(conn: Any, sql: str, params: tuple = ()) -> list:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()

def insert_rows(conn: Any, sql: str, rows: list) -> int:
    cur = conn.cursor()
    try:
        cur.executemany(sql, rows)
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
