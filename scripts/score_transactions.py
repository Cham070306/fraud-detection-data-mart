from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from src.scoring.score import score_transactions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--policy", default="configs/risk_policy.yaml")
    parser.add_argument("--output", default="output/model_scoring_sample.csv")
    parser.add_argument("--rows", type=int, default=None)
    args = parser.parse_args()
    metadata = json.loads(Path(args.metadata).read_text(encoding="utf-8"))
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    usecols = ["step", "type", "amount", "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"]
    dtypes = {"step":"int16", "type":"category", "amount":"float32", "oldbalanceOrg":"float32", "newbalanceOrig":"float32", "oldbalanceDest":"float32", "newbalanceDest":"float32"}
    remaining = args.rows
    total = 0
    first = True
    for frame in pd.read_csv(args.input, usecols=usecols, dtype=dtypes, chunksize=200_000):
        if remaining is not None:
            frame = frame.iloc[:remaining]
        if frame.empty:
            break
        scored = score_transactions(frame, args.model, metadata, args.policy)
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
