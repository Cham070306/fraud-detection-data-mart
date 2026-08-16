from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd

from src.training.train import save_model, train_models


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", default="models")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--rows", type=int, default=None, help="Optional development row limit")
    parser.add_argument("--evaluation-dir", default="output/evaluation")
    args = parser.parse_args()
    dtypes = {
        "step": "int16", "type": "category", "amount": "float32",
        "oldbalanceOrg": "float32", "newbalanceOrig": "float32",
        "oldbalanceDest": "float32", "newbalanceDest": "float32",
        "isFraud": "int8", "isFlaggedFraud": "int8",
    }
    frame = pd.read_csv(args.input, usecols=list(dtypes), dtype=dtypes, nrows=args.rows)
    selected_name, results = train_models(frame)
    artifact, metadata = save_model(selected_name, results[selected_name], args.output_dir, args.version, training_data_source=str(Path(args.input).resolve()))
    evaluation_dir = Path(args.evaluation_dir)
    evaluation_dir.mkdir(parents=True, exist_ok=True)
    comparison = pd.DataFrame([
        {"model": name, "training_rows": value["training_rows"], **value["validation"]}
        for name, value in results.items()
    ])
    comparison.to_csv(evaluation_dir / "model_comparison.csv", index=False)
    summary = {name: {"training_rows": value["training_rows"], **value["validation"]} for name, value in results.items()}
    print(json.dumps({"selected": selected_name, "artifact": str(artifact), "validation": summary, "test": metadata["test_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
