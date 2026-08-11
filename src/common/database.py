from __future__ import annotations
import pyodbc
from typing import Iterator, Any, Optional
from src.common.config import AppConfig, DatabaseConfig

def get_connection(cfg: AppConfig | DatabaseConfig | None = None) -> pyodbc.Connection:
    if cfg is None:
        cfg = AppConfig.load()
    if isinstance(cfg, AppConfig):
        db_cfg = cfg.db
    else:
        db_cfg = cfg
    return pyodbc.connect(db_cfg.connection_string(), autocommit=False)

def execute(conn: pyodbc.Connection, sql: str, params: tuple = ()) -> None:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def query(conn: pyodbc.Connection, sql: str, params: tuple = ()) -> list:
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()

def insert_rows(conn: pyodbc.Connection, sql: str, rows: list) -> int:
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
