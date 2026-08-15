#!/usr/bin/env python
"""Backup FraudDW to SQL Server default backup folder (avoid Access denied)."""
import io, sys, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os

import pyodbc

server = os.getenv("FRAUD_DB_SERVER", r"localhost\SQLEXPRESS")
database = os.getenv("FRAUD_DB_NAME", "FraudDW")
conn = pyodbc.connect(
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE=master;"
    "Trusted_Connection=yes;TrustServerCertificate=yes;timeout=60"
)
conn.autocommit = True
cur = conn.cursor()

# Get default backup dir from registry
cur.execute("""
    EXEC master.dbo.xp_instance_regread
        N'HKEY_LOCAL_MACHINE',
        N'Software\\Microsoft\\MSSQLServer\\MSSQLServer',
        N'BackupDirectory'
""")
rows = cur.fetchall()
bak_dir = None
for r in rows:
    if r[1] and str(r[1]).strip():
        bak_dir = str(r[1]).strip()
        break
if not bak_dir:
    bak_dir = r"C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\Backup"

ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
bak_path = bak_dir.rstrip('\\') + f"\\{database}_backup_{ts}.bak"

sql = f"BACKUP DATABASE [{database}] TO DISK = N'{bak_path}' WITH FORMAT, INIT, NAME = N'{database}-Full-Backup'"
print(f"Backup dir: {bak_dir}")
print(f"Running: BACKUP DATABASE {database} -> {bak_path}")
cur.execute(sql)

# Verify from msdb
cur.execute("""
    SELECT TOP 1 m.physical_device_name, b.backup_finish_date
    FROM msdb.dbo.backupset b
    JOIN msdb.dbo.backupmediafamily m ON b.media_set_id = m.media_set_id
    WHERE b.database_name = ?
    ORDER BY b.backup_finish_date DESC
""", database)
row = cur.fetchone()
if row:
    print(f"Verify OK: device={row[0]}, finish={row[1]}")

cur.close()
conn.close()
print("BACKUP_DONE")
print(f"BACKUP_PATH={bak_path}")
