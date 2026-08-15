from __future__ import annotations

from src.common.logger import get_logger

logger = get_logger("etl.load_facts")

_CREATE_FACT_TEMP_SQL = """
DROP TABLE IF EXISTS #FactInput;
CREATE TABLE #FactInput (
 DateKey INT NOT NULL, TimeKey INT NOT NULL, TransactionTypeKey INT NOT NULL,
 OrigAccountKey INT NOT NULL, DestAccountKey INT NOT NULL, AmountBandKey INT NOT NULL,
 StepRaw INT NOT NULL, Amount DECIMAL(18,2) NOT NULL,
 OldBalanceOrig DECIMAL(18,2) NOT NULL, NewBalanceOrig DECIMAL(18,2) NOT NULL,
 OldBalanceDest DECIMAL(18,2) NOT NULL, NewBalanceDest DECIMAL(18,2) NOT NULL,
 IsFraud BIT NOT NULL, IsFlaggedFraud BIT NOT NULL
)
"""
_DROP_FACT_TEMP_SQL = "DROP TABLE IF EXISTS #FactInput"
_INSERT_FACT_TEMP_SQL = (
    "INSERT INTO #FactInput VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_INSERT_NEW_FACTS_SQL = """
INSERT INTO fact.FactTransaction (
 DateKey, TimeKey, TransactionTypeKey, OrigAccountKey, DestAccountKey, AmountBandKey,
 StepRaw, Amount, OldBalanceOrig, NewBalanceOrig, OldBalanceDest, NewBalanceDest,
 IsFraud, IsFlaggedFraud)
SELECT DISTINCT i.DateKey, i.TimeKey, i.TransactionTypeKey, i.OrigAccountKey,
       i.DestAccountKey, i.AmountBandKey, i.StepRaw, i.Amount,
       i.OldBalanceOrig, i.NewBalanceOrig, i.OldBalanceDest, i.NewBalanceDest,
       i.IsFraud, i.IsFlaggedFraud
FROM #FactInput AS i
WHERE NOT EXISTS (
 SELECT 1 FROM fact.FactTransaction AS f WITH (UPDLOCK, HOLDLOCK)
 WHERE f.DateKey=i.DateKey AND f.TimeKey=i.TimeKey
   AND f.TransactionTypeKey=i.TransactionTypeKey
   AND f.OrigAccountKey=i.OrigAccountKey AND f.DestAccountKey=i.DestAccountKey
   AND f.AmountBandKey=i.AmountBandKey AND f.StepRaw=i.StepRaw
   AND f.Amount=i.Amount AND f.OldBalanceOrig=i.OldBalanceOrig
   AND f.NewBalanceOrig=i.NewBalanceOrig AND f.OldBalanceDest=i.OldBalanceDest
   AND f.NewBalanceDest=i.NewBalanceDest AND f.IsFraud=i.IsFraud
   AND f.IsFlaggedFraud=i.IsFlaggedFraud
);
SELECT @@ROWCOUNT;
"""


def load_fact_transaction(conn, df_transformed, lookups, batch_id):
    """Insert only business-distinct transactions; one chunk is atomic."""
    account_map, type_map, band_map = (lookups["account"], lookups["type"], lookups["band"])
    rows = [(
        int(r.DateKey), int(r.TimeKey), int(type_map[r.TypeCode]),
        int(account_map[r.NameOrig]), int(account_map[r.NameDest]), int(band_map[r.BandCode]),
        int(r.StepRaw), float(r.Amount), float(r.OldBalanceOrig), float(r.NewBalanceOrig),
        float(r.OldBalanceDest), float(r.NewBalanceDest), int(r.IsFraud), int(r.IsFlaggedFraud),
    ) for r in df_transformed.itertuples(index=False)]
    if not rows:
        return 0

    cur = conn.cursor()
    try:
        cur.execute(_CREATE_FACT_TEMP_SQL)
        cur.executemany(_INSERT_FACT_TEMP_SQL, rows)
        cur.execute(_INSERT_NEW_FACTS_SQL)
        inserted = int(cur.fetchone()[0])
        conn.commit()
        logger.info("Fact batch=%s received=%s inserted=%s already_loaded=%s",
                    batch_id, len(rows), inserted, len(rows) - inserted)
        return inserted
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.execute(_DROP_FACT_TEMP_SQL)
        except Exception:
            logger.warning("Could not drop #FactInput during cleanup", exc_info=True)
        cur.close()
