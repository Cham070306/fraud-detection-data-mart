from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.load_ml_results import load_scoring_results


def main():
    parser = argparse.ArgumentParser(description="Load ML scores and alerts into FraudDW")
    parser.add_argument("--scores", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--policy", default="configs/risk_policy.yaml")
    parser.add_argument("--chunk-size", type=int, default=50_000)
    args = parser.parse_args()
    result = load_scoring_results(
        args.scores, args.metadata, args.policy, chunk_size=args.chunk_size
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
