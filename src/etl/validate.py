from __future__ import annotations
import pandas as pd
from src.common.config import VALID_TYPES

def validate_chunk(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    reasons = pd.Series([''] * len(df), index=df.index)

    required = [
        'step', 'type', 'amount', 'nameOrig', 'oldbalanceOrg', 'newbalanceOrig',
        'nameDest', 'oldbalanceDest', 'newbalanceDest', 'isFraud', 'isFlaggedFraud',
    ]
    null_required = df[required].isna().any(axis=1)
    reasons[null_required] += 'null_required;'

    invalid_type = ~df['type'].isin(VALID_TYPES)
    reasons[invalid_type] += 'invalid_type;'

    neg_amount = df['amount'].fillna(0) < 0
    reasons[neg_amount] += 'negative_amount;'

    bad_fraud = ~df['isFraud'].isin([0, 1])
    reasons[bad_fraud] += 'invalid_isFraud;'

    bad_flag = ~df['isFlaggedFraud'].isin([0, 1])
    reasons[bad_flag] += 'invalid_isFlaggedFraud;'

    bad_orig = ~df['nameOrig'].fillna('').astype(str).str.fullmatch(r'[CM]\d{1,19}')
    reasons[bad_orig] += 'invalid_orig_account;'

    bad_dest = ~df['nameDest'].fillna('').astype(str).str.fullmatch(r'[CM]\d{1,19}')
    reasons[bad_dest] += 'invalid_dest_account;'

    numeric_step = pd.to_numeric(df['step'], errors='coerce')
    bad_step = numeric_step.isna() | (numeric_step < 1) | (numeric_step > 744) | (numeric_step % 1 != 0)
    reasons[bad_step] += 'invalid_step;'

    is_valid = reasons == ''
    valid_df = df[is_valid].copy()
    reject_df = df[~is_valid].copy()
    reject_df['RejectReason'] = reasons[~is_valid]
    return valid_df, reject_df
