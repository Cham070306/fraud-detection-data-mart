from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from src.decision.alert_generator import ALERT_COLUMNS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", required=True); parser.add_argument("--output", default="output/fact_alert_v1.0.0.csv")
    args = parser.parse_args(); output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    first = True; total = 0
    for chunk in pd.read_csv(args.scores, chunksize=200_000):
        alerts = chunk.loc[chunk["CreateAlert"], ALERT_COLUMNS].drop_duplicates(["TransactionKey", "ModelVersion"])
        alerts.to_csv(output, mode="w" if first else "a", header=first, index=False)
        first = False; total += len(alerts)
    print(f"Wrote {total:,} alerts to {output}")


if __name__ == "__main__": main()
