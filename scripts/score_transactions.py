from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from src.common.database import get_connection
from src.scoring.score import score_transactions


SCORE_COLUMNS = [
    "TransactionKey", "DateKey", "TimeKey", "step", "type", "amount",
    "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest",
]


def iter_sql_frames(chunk_size: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ft.TransactionKey, ft.DateKey, ft.TimeKey, ft.StepRaw AS step,
               tt.TypeCode AS type, ft.Amount AS amount,
               ft.OldBalanceOrig AS oldbalanceOrg,
               ft.NewBalanceOrig AS newbalanceOrig,
               ft.OldBalanceDest AS oldbalanceDest,
               ft.NewBalanceDest AS newbalanceDest
        FROM fact.FactTransaction AS ft
        JOIN dim.DimTransactionType AS tt
          ON tt.TransactionTypeKey = ft.TransactionTypeKey
        ORDER BY ft.TransactionKey
        """
    )
    columns = [item[0] for item in cur.description]
    try:
        while True:
            rows = cur.fetchmany(chunk_size)
            if not rows:
                break
            yield pd.DataFrame.from_records(rows, columns=columns)
    finally:
        cur.close()
        conn.close()


def iter_csv_frames(path: str, chunk_size: int):
    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = sorted(set(SCORE_COLUMNS) - set(header))
    if missing:
        raise ValueError(
            "Production scoring CSV must contain SQL transaction keys. "
            f"Missing columns: {missing}. Prefer --from-sql."
        )
    yield from pd.read_csv(path, usecols=SCORE_COLUMNS, chunksize=chunk_size)


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input")
    source.add_argument("--from-sql", action="store_true")
    parser.add_argument("--model", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--policy", default="configs/risk_policy.yaml")
    parser.add_argument("--output", default="output/model_scoring_sample.csv")
    parser.add_argument("--rows", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=200_000)
    parser.add_argument("--start-date", default="2023-01-01")
    args = parser.parse_args()
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    remaining = args.rows
    total = 0
    first = True
    frames = iter_sql_frames(args.chunk_size) if args.from_sql else iter_csv_frames(
        args.input, args.chunk_size
    )
    for frame in frames:
        if remaining is not None:
            frame = frame.iloc[:remaining]
        if frame.empty:
            break
        scored = score_transactions(
            frame, args.model, metadata, args.policy, start_date=args.start_date
        )
        scored.to_csv(output, mode="w" if first else "a", header=first, index=False)
        first = False
        total += len(scored)
        print(f"Scored {total:,} rows")
        if remaining is not None:
            remaining -= len(frame)
            if remaining <= 0:
                break
    print(f"Wrote {total:,} rows to {output}")


if __name__ == "__main__":
    main()
