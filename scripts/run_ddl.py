#!/usr/bin/env python
"""Run 01..07 DDL files against FraudDW via pyodbc (sqlcmd not on PATH)."""
import io
import os
import sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import pyodbc

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
FILES = [
    "01_create_schemas.sql",
    "02_create_staging_tables.sql",
    "03_create_dimensions.sql",
    "04_create_fact_tables.sql",
    "05_create_constraints_indexes.sql",
    "06_create_bi_views.sql",
    "07_seed_dimensions.sql",
]

server = os.getenv("FRAUD_DB_SERVER", r"localhost\SQLEXPRESS")
database = os.getenv("FRAUD_DB_NAME", "FraudDW")
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};"
    "Trusted_Connection=yes;TrustServerCertificate=yes"
)
conn.autocommit = True
cur = conn.cursor()

for fname in FILES:
    path = SQL_DIR / fname
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    # split on GO batch separator
    batches = [b.strip() for b in content.split('\nGO') if b.strip()]
    for b in batches:
        try:
            cur.execute(b)
        except Exception as e:
            print(f"[ERROR] {fname}: {e}")
            print(f"  batch head: {b[:200]!r}")
    print(f"[OK] {fname} -> {len(batches)} batches executed")

# verify
cur.execute("""
    SELECT s.name AS schema_name, COUNT(o.object_id) AS obj_count
    FROM sys.schemas s
    LEFT JOIN sys.objects o ON o.schema_id = s.schema_id
    WHERE s.name IN ('stg','dim','fact','audit')
    GROUP BY s.name ORDER BY s.name
""")
print("\nSchema object counts in FraudDW:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

cur.close()
conn.close()
