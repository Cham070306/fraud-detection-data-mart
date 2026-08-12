from __future__ import annotations
import pandas as pd
from src.common.config import VALID_TYPES

def validate_chunk(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    reasons = pd.Series([''] * len(df), index=df.index)

    invalid_type = ~df['type'].isin(VALID_TYPES)
    reasons[invalid_type] += 'invalid_type;'

    neg_amount = df['amount'] < 0
    reasons[neg_amount] += 'negative_amount;'

    bad_fraud = ~df['isFraud'].isin([0, 1])
    reasons[bad_fraud] += 'invalid_isFraud;'

    bad_flag = ~df['isFlaggedFraud'].isin([0, 1])
    reasons[bad_flag] += 'invalid_isFlaggedFraud;'

    bad_orig = ~df['nameOrig'].astype(str).str[0].isin(['C', 'M'])
    reasons[bad_orig] += 'invalid_orig_account;'

    bad_dest = ~df['nameDest'].astype(str).str[0].isin(['C', 'M'])
    reasons[bad_dest] += 'invalid_dest_account;'

    bad_step = df['step'] < 1
    reasons[bad_step] += 'invalid_step;'

    is_valid = reasons == ''
    valid_df = df[is_valid].copy()
    reject_df = df[~is_valid].copy()
    reject_df['RejectReason'] = reasons[~is_valid]
    return valid_df, reject_df
