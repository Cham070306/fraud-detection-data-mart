from __future__ import annotations

from collections.abc import Iterable

from src.common.logger import get_logger
from src.common.database import query

logger = get_logger("etl.load_dimensions")

_CREATE_ACCOUNT_TEMP_SQL = (
    "DROP TABLE IF EXISTS #AccountInput; "
    "CREATE TABLE #AccountInput (AccountID VARCHAR(20) NOT NULL PRIMARY KEY)"
)
_DROP_ACCOUNT_TEMP_SQL = "DROP TABLE IF EXISTS #AccountInput"
_INSERT_MISSING_ACCOUNTS_SQL = """
DECLARE @max_key INT;
SELECT @max_key = ISNULL(MAX(AccountKey), 0)
FROM dim.DimAccount WITH (UPDLOCK, HOLDLOCK);
INSERT INTO dim.DimAccount (AccountKey, AccountID, AccountType)
SELECT @max_key + ROW_NUMBER() OVER (ORDER BY src.AccountID),
       src.AccountID, LEFT(src.AccountID, 1)
FROM #AccountInput AS src
LEFT JOIN dim.DimAccount AS existing WITH (UPDLOCK, HOLDLOCK)
  ON existing.AccountID = src.AccountID
WHERE existing.AccountID IS NULL;
SELECT @@ROWCOUNT;
"""
_SELECT_ACCOUNT_MAPPING_SQL = """
SELECT d.AccountID, d.AccountKey
FROM dim.DimAccount AS d
JOIN #AccountInput AS src ON src.AccountID = d.AccountID
"""


def chunked(values, batch_size):
    """Yield fixed-size lists for bounded executemany calls."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    for start in range(0, len(values), batch_size):
        yield values[start:start + batch_size]


def normalize_account_ids(account_ids: Iterable) -> list[str]:
    """Flatten nested inputs, remove invalid values and de-duplicate in order."""
    normalized = []
    seen = set()

    def visit(value):
        if isinstance(value, (list, tuple, set)):
            for nested in value:
                visit(nested)
            return
        if value is None or not isinstance(value, str):
            return
        account_id = value.strip()
        if (not account_id or len(account_id) > 20 or account_id[0] not in {"C", "M"}
                or not account_id[1:].isdigit() or account_id in seen):
            return
        seen.add(account_id)
        normalized.append(account_id)

    visit(account_ids)
    return normalized


def ensure_accounts(conn, account_ids, batch_size=1000):
    """Ensure accounts exist and return AccountID -> stable surrogate key.

    Each executemany execution contains one marker. The 1,000-row client batch
    therefore stays comfortably below SQL Server's 2,100 parameter limit.
    """
    received_count = len(account_ids) if hasattr(account_ids, "__len__") else None
    values = normalize_account_ids(account_ids)
    if not values:
        logger.info("Accounts received=%s unique_valid=0 existing=0 inserted=0", received_count or 0)
        return {}

    cur = conn.cursor()
    try:
        cur.execute(_CREATE_ACCOUNT_TEMP_SQL)
        for batch in chunked(values, batch_size):
            cur.executemany("INSERT INTO #AccountInput (AccountID) VALUES (?)",
                            [(account_id,) for account_id in batch])
        cur.execute(_INSERT_MISSING_ACCOUNTS_SQL)
        inserted = int(cur.fetchone()[0])
        cur.execute(_SELECT_ACCOUNT_MAPPING_SQL)
        mapping = {row[0]: row[1] for row in cur.fetchall()}
        if len(mapping) != len(values):
            missing = set(values) - set(mapping)
            raise RuntimeError(f"DimAccount lookup missing {len(missing)} account(s)")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            cur.execute(_DROP_ACCOUNT_TEMP_SQL)
        except Exception:
            logger.warning("Could not drop #AccountInput during cleanup", exc_info=True)
        cur.close()

    existing = len(values) - inserted
    logger.info("Accounts received=%s unique_valid=%s existing=%s inserted=%s",
                received_count if received_count is not None else "unknown",
                len(values), existing, inserted)
    return mapping


def get_lookup_keys(conn):
    type_rows = query(conn, "SELECT TypeCode, TransactionTypeKey FROM dim.DimTransactionType")
    band_rows = query(conn, "SELECT BandCode, AmountBandKey FROM dim.DimAmountBand")
    return {"type": {r[0]: r[1] for r in type_rows},
            "band": {r[0]: r[1] for r in band_rows}}


def load_dimensions_for_chunk(conn, df_transformed):
    account_ids = df_transformed["NameOrig"].tolist() + df_transformed["NameDest"].tolist()
    account_map = ensure_accounts(conn, account_ids)
    lookups = get_lookup_keys(conn)
    return {"account": account_map, "type": lookups["type"], "band": lookups["band"]}
