from __future__ import annotations
import pandas as pd
import pyodbc
from src.common.logger import get_logger
from src.common.database import query, execute

logger = get_logger("etl.load_dimensions")

_INSERT_ACCOUNT_SQL = (
    "IF NOT EXISTS (SELECT 1 FROM dim.DimAccount WHERE AccountID = ?) "
    "BEGIN "
    "  DECLARE @next INT; "
    "  SELECT @next = ISNULL(MAX(AccountKey), 0) + 1 FROM dim.DimAccount; "
    "  INSERT INTO dim.DimAccount (AccountKey, AccountID, AccountType) "
    "  VALUES (@next, ?, LEFT(?, 1)); "
    "END"
)


def ensure_accounts(conn, account_ids):
    """Bao dam moi AccountID ton tai trong DimAccount, tra ve mapping id->key."""
    cur = conn.cursor()
    mapping = {}
    try:
        for aid in account_ids:
            cur.execute(_INSERT_ACCOUNT_SQL, (aid, aid, aid))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    placeholders = ",".join(["?"] * len(account_ids))
    sql = (
        "SELECT AccountID, AccountKey FROM dim.DimAccount "
        f"WHERE AccountID IN ({placeholders})"
    )
    rows = query(conn, sql, tuple(account_ids))
    for row in rows:
        mapping[row[0]] = row[1]
    return mapping


def get_lookup_keys(conn):
    type_rows = query(conn, "SELECT TypeCode, TransactionTypeKey FROM dim.DimTransactionType")
    band_rows = query(conn, "SELECT BandCode, AmountBandKey FROM dim.DimAmountBand")
    return {
        "type": {r[0]: r[1] for r in type_rows},
        "band": {r[0]: r[1] for r in band_rows},
    }


def load_dimensions_for_chunk(conn, df_transformed):
    account_ids = list(
        set(df_transformed["NameOrig"].tolist() + df_transformed["NameDest"].tolist())
    )
    logger.info(f"Loading {len(account_ids)} accounts")
    account_map = ensure_accounts(conn, account_ids)
    lookups = get_lookup_keys(conn)
    return {
        "account": account_map,
        "type": lookups["type"],
        "band": lookups["band"],
    }
