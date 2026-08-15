#!/usr/bin/env python
"""Run validation queries against FraudDW (equivalent of sql/08_validation_queries.sql)."""
import io
import os
import sys

import pyodbc
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

server = os.getenv("FRAUD_DB_SERVER", r"localhost\SQLEXPRESS")
database = os.getenv("FRAUD_DB_NAME", "FraudDW")
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};"
    "Trusted_Connection=yes;TrustServerCertificate=yes"
)
cur = conn.cursor()

print('=== VALIDATION QUERIES (FraudDW) ===')
print()

cur.execute('SELECT COUNT_BIG(*) FROM stg.TransactionRaw')
print(f'stg.TransactionRaw: {cur.fetchone()[0]:,}')
cur.execute('SELECT COUNT_BIG(*) FROM fact.FactTransaction')
print(f'fact.FactTransaction: {cur.fetchone()[0]:,}')
cur.execute('SELECT COUNT_BIG(*) FROM fact.FactModelScore')
print(f'fact.FactModelScore: {cur.fetchone()[0]:,}')
cur.execute('SELECT COUNT_BIG(*) FROM fact.FactAlert')
print(f'fact.FactAlert: {cur.fetchone()[0]:,}')
print()

cur.execute('SELECT IsFraud, COUNT_BIG(*) FROM fact.FactTransaction GROUP BY IsFraud')
print('Fraud breakdown:')
for r in cur.fetchall():
    print(f'  IsFraud={r[0]}: {r[1]:,}')
print()

cur.execute('SELECT COUNT_BIG(*), SUM(CASE WHEN IsFraud=1 THEN 1 ELSE 0 END), SUM(CASE WHEN IsFlaggedFraud=1 THEN 1 ELSE 0 END) FROM fact.FactTransaction')
r = cur.fetchone()
print(f'EDA-01 reconciliation: Total={r[0]:,}, Fraud={r[1]:,}, Flagged={r[2]:,}')
print()

cur.execute('SELECT SUM(Amount), SUM(CASE WHEN IsFraud=1 THEN Amount ELSE 0 END) FROM fact.FactTransaction')
r = cur.fetchone()
print(f'Amount: Total={r[0]:,.2f}, Fraud={r[1]:,.2f}')
print()

cur.execute('SELECT COUNT_BIG(*) FROM fact.FactTransaction f LEFT JOIN dim.DimDate d ON f.DateKey=d.DateKey WHERE d.DateKey IS NULL')
print(f'Orphan FK (DateKey): {cur.fetchone()[0]}')
print()

cur.close()
conn.close()
print('VALIDATION DONE')
