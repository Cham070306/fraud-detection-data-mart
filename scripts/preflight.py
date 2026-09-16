#!/usr/bin/env python
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.common.config import AppConfig


def main() -> int:
    cfg = AppConfig.load()
    checks = {
        "python_3_11_or_newer": sys.version_info >= (3, 11),
        "config_exists": (PROJECT_ROOT / "configs/app.yaml").exists(),
        "dataset_exists": cfg.paysim_file.exists(),
        "risk_policy_exists": (PROJECT_ROOT / "configs/risk_policy.yaml").exists(),
        "sql_files_complete": all((PROJECT_ROOT / f"sql/{i:02d}_{name}").exists() for i, name in [
            (0, "create_database.sql"), (1, "create_schemas.sql"),
            (2, "create_staging_tables.sql"), (3, "create_dimensions.sql"),
            (4, "create_fact_tables.sql"), (5, "create_constraints_indexes.sql"),
            (6, "create_bi_views.sql"), (7, "seed_dimensions.sql"),
        ]),
    }
    try:
        import pyodbc
        checks["pyodbc_installed"] = True
        checks["configured_odbc_driver_installed"] = cfg.db.driver in pyodbc.drivers()
    except ImportError:
        checks["pyodbc_installed"] = False
        checks["configured_odbc_driver_installed"] = False

    result = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "database_server": cfg.db.server,
        "database_name": cfg.db.database,
        "dataset": str(cfg.paysim_file),
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
