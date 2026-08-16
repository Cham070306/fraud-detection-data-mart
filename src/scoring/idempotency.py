from __future__ import annotations
import pandas as pd


def only_new_scores(scored: pd.DataFrame, existing: pd.DataFrame | None = None) -> pd.DataFrame:
    """Enforce the FactModelScore natural key: TransactionKey + ModelVersion."""
    keys = ["TransactionKey", "ModelVersion"]
    missing = sorted(set(keys) - set(scored.columns))
    if missing:
        raise ValueError(f"Missing score key columns: {missing}")
    result = scored.drop_duplicates(keys, keep="first")
    if existing is not None and not existing.empty:
        existing_keys = pd.MultiIndex.from_frame(existing[keys])
        candidate_keys = pd.MultiIndex.from_frame(result[keys])
        result = result.loc[~candidate_keys.isin(existing_keys)]
    return result.reset_index(drop=True)
