from __future__ import annotations
from src.common.config import AppConfig
from src.common.logger import get_logger
from src.common.database import get_connection, execute
from src.etl.extract import extract_chunks
from src.etl.validate import validate_chunk
from src.etl.transform import transform_chunk
from src.etl.load_dimensions import load_dimensions_for_chunk
from src.etl.load_facts import load_fact_transaction
from src.etl.reconciliation import reconcile, log_reconciliation

logger = get_logger("etl.run")

_INSERT_STAGING_SQL = (
    "INSERT INTO stg.TransactionRaw ("
    " BatchID, SourceFileName, RowNumberInChunk, StepRaw, TypeCode, Amount,"
    " NameOrig, OldBalanceOrg, NewBalanceOrig, NameDest, OldBalanceDest,"
    " NewBalanceDest, IsFraud, IsFlaggedFraud"
    ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)


def init_batch(conn, source_file):
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO audit.ETLBatchLog (SourceFileName, Status, StartedAt) "
            "OUTPUT INSERTED.BatchID VALUES (?, 'RUNNING', SYSDATETIME())",
            (source_file,),
        )
        batch_id = cur.fetchone()[0]
        conn.commit()
        return int(batch_id)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def finalize_batch(conn, batch_id, status, message=""):
    execute(
        conn,
        "UPDATE audit.ETLBatchLog SET Status=?, FinishedAt=SYSDATETIME(), Message=? WHERE BatchID=?",
        (status, message, batch_id),
    )


def _load_staging(conn, chunk, batch_id, source_name, chunk_idx, chunk_size):
    rows = []
    base = chunk_idx * chunk_size
    for i, r in enumerate(chunk.itertuples(index=False)):
        rows.append((
            batch_id, source_name, base + i,
            int(r.step), str(r.type), float(r.amount),
            str(r.nameOrig), float(r.oldbalanceOrg), float(r.newbalanceOrig),
            str(r.nameDest), float(r.oldbalanceDest), float(r.newbalanceDest),
            int(r.isFraud), int(r.isFlaggedFraud),
        ))
    cur = conn.cursor()
    try:
        cur.executemany(_INSERT_STAGING_SQL, rows)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _log_rejects(conn, reject_rows_all):
    if not reject_rows_all:
        return
    cur = conn.cursor()
    try:
        cur.executemany(
            "INSERT INTO audit.RejectLog (BatchID, SourceFileName, ChunkIndex, StepRaw, Reason) "
            "VALUES (?, ?, ?, ?, ?)",
            reject_rows_all,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def run_pipeline(cfg=None, load_staging=True):
    cfg = cfg or AppConfig.load()
    logger.info("Bat dau pipeline ETL")
    conn = get_connection(cfg)
    batch_id = None
    try:
        source_name = cfg.paysim_file.name
        batch_id = init_batch(conn, str(cfg.paysim_file))
        logger.info(f"BatchID = {batch_id}")

        total_source = 0
        total_valid = 0
        total_reject = 0
        total_fact = 0
        total_amount = 0.0
        total_fraud = 0
        reject_rows_all = []

        for chunk_idx, chunk in enumerate(extract_chunks(cfg)):
            total_source += len(chunk)
            if load_staging:
                _load_staging(conn, chunk, batch_id, source_name, chunk_idx, cfg.chunk_size)

            valid, reject = validate_chunk(chunk)
            total_valid += len(valid)
            total_reject += len(reject)
            for _, r in reject.iterrows():
                reject_rows_all.append((
                    batch_id, source_name, chunk_idx,
                    int(r.get("step", -1)), str(r.get("RejectReason", "")),
                ))

            transformed = transform_chunk(valid, start_date=cfg.start_date)
            total_amount += float(transformed["Amount"].sum())
            total_fraud += int(transformed["IsFraud"].sum())

            lookups = load_dimensions_for_chunk(conn, transformed)
            inserted = load_fact_transaction(conn, transformed, lookups, batch_id)
            total_fact += inserted
            logger.info(
                f"Chunk {chunk_idx}: source={len(chunk)} valid={len(valid)} "
                f"reject={len(reject)} fact={inserted}"
            )

        _log_rejects(conn, reject_rows_all)

        result = reconcile(conn, batch_id, total_valid, total_amount, total_fraud)
        log_reconciliation(conn, result)
        status = "SUCCESS" if result["status"] == "PASS" else "FAIL"
        finalize_batch(conn, batch_id, status, f"fact={total_fact}, reject={total_reject}")
        logger.info(f"Pipeline hoan thanh: {status}")

        return {
            "batch_id": batch_id,
            "status": status,
            "source_rows": total_source,
            "valid_rows": total_valid,
            "reject_rows": total_reject,
            "fact_rows": total_fact,
            "amount_sum": total_amount,
            "fraud_count": total_fraud,
            "reconciliation": result,
        }
    except Exception as e:
        logger.exception(f"Pipeline loi: {e}")
        try:
            if batch_id is not None:
                finalize_batch(conn, batch_id, "ERROR", str(e))
        except Exception:
            pass
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    summary = run_pipeline()
    print(summary)
