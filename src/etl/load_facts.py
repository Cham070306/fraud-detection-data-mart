from __future__ import annotations
import pandas as pd
import pyodbc
from src.common.logger import get_logger

logger = get_logger("etl.load_facts")

INSERT_FACT_SQL = (
    "INSERT INTO fact.FactTransaction ("
    " DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey, AmountBandKey,"
    " StepRaw, Amount, OldBalanceOrig, NewBalanceOrig, OldBalanceDest, NewBalanceDest,"
    " IsFraud, IsFlaggedFraud"
    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def load_fact_transaction(conn, df_transformed, lookups, batch_id):
    """Nap du lieu tu DataFrame da transform vao fact.FactTransaction."""
    account_map = lookups["account"]
    type_map = lookups["type"]
    band_map = lookups["band"]
    rows = []
    for r in df_transformed.itertuples(index=False):
        rows.append((
            int(r.DateKey),
            int(r.TimeKey),
            int(type_map[r.TypeCode]),
            int(account_map[r.NameOrig]),
            int(account_map[r.NameDest]),
            int(band_map[r.BandCode]),
            int(r.StepRaw),
            float(r.Amount),
            float(r.OldBalanceOrig),
            float(r.NewBalanceOrig),
            float(r.OldBalanceDest),
            float(r.NewBalanceDest),
            int(r.IsFraud),
            int(r.IsFlaggedFraud),
        ))
    cur = conn.cursor()
    try:
        cur.executemany(INSERT_FACT_SQL, rows)
        conn.commit()
        logger.info(f"Inserted {len(rows)} rows into fact.FactTransaction (batch {batch_id})")
        return len(rows)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
