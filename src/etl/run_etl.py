from __future__ import annotations
import argparse
from pathlib import Path
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
    if chunk.empty:
        return
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
        if hasattr(cur, "fast_executemany"):
            cur.fast_executemany = True
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
        if hasattr(cur, "fast_executemany"):
            cur.fast_executemany = True
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


def _safe_step(value):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def run_pipeline(cfg=None):
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
        total_inserted = 0
        total_amount = 0.0
        total_fraud = 0
        reject_rows_all = []

        for chunk_idx, chunk in enumerate(extract_chunks(cfg)):
            total_source += len(chunk)
            valid, reject = validate_chunk(chunk, max_step=cfg.max_step)
            total_valid += len(valid)
            total_reject += len(reject)
            # The staging schema is typed and NOT NULL, so rejected raw values
            # belong in RejectLog; loading them first would fail before DQ can
            # record the real rejection reason.
            _load_staging(conn, valid, batch_id, source_name, chunk_idx, cfg.chunk_size)
            for _, r in reject.iterrows():
                reject_rows_all.append((
                    batch_id, source_name, chunk_idx,
                    _safe_step(r.get("step")), str(r.get("RejectReason", "")),
                ))

            transformed = transform_chunk(valid, start_date=cfg.start_date)
            total_amount += float(transformed["Amount"].sum())
            total_fraud += int(transformed["IsFraud"].sum())

            lookups = load_dimensions_for_chunk(conn, transformed)
            inserted = load_fact_transaction(conn, transformed, lookups, batch_id)
            total_inserted += inserted
            logger.info(
                f"Chunk {chunk_idx}: source={len(chunk)} valid={len(valid)} "
                f"reject={len(reject)} fact={inserted}"
            )

        _log_rejects(conn, reject_rows_all)

        result = reconcile(
            conn, batch_id, total_valid, total_amount, total_fraud,
            inserted_rows=total_inserted,
        )
        log_reconciliation(conn, result)
        accounting_pass = total_source == total_valid + total_reject
        error_rate = total_reject / total_source if total_source else 0.0
        within_tolerance = error_rate <= cfg.max_validation_error_rate
        if result["status"] == "PASS" and accounting_pass and within_tolerance:
            status = "SUCCESS" if total_reject == 0 else "SUCCESS_WARN"
        else:
            status = "FAIL"
        finalize_batch(
            conn, batch_id, status,
            (f"source={total_source}, valid={total_valid}, reject={total_reject}, "
             f"error_rate={error_rate:.6f}, "
             f"inserted={total_inserted}, existing={result['existing_rows']}, "
             f"matched_fact={result['final_fact_rows']}")
        )
        logger.info(f"Pipeline hoan thanh: {status}")

        return {
            "batch_id": batch_id,
            "status": status,
            "source_rows": total_source,
            "valid_rows": total_valid,
            "rejected_rows": total_reject,
            "reject_rows": total_reject,
            "validation_error_rate": error_rate,
            "inserted_rows": total_inserted,
            "existing_rows": result["existing_rows"],
            "final_fact_rows": result["final_fact_rows"],
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


def main():
    parser = argparse.ArgumentParser(description="Run the PaySim ETL pipeline")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--chunk-size", type=int)
    args = parser.parse_args()
    cfg = AppConfig.load(args.config)
    if args.input:
        cfg.paysim_file = args.input
    if args.chunk_size:
        if args.chunk_size < 1:
            parser.error("--chunk-size must be positive")
        cfg.chunk_size = args.chunk_size
    summary = run_pipeline(cfg)
    print(summary)


if __name__ == "__main__":
    main()
