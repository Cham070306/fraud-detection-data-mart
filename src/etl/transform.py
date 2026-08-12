from __future__ import annotations
import pandas as pd
from datetime import datetime, timedelta
from src.common.config import AMOUNT_BANDS, HIGH_RISK_TYPES, DEFAULT_START_DATE

def amount_band_code(amount: float) -> str:
    for code, low, high in AMOUNT_BANDS:
        if high is None:
            if amount >= low:
                return code
        elif low <= amount < high:
            return code
    return 'XXL'

def transform_chunk(df: pd.DataFrame, start_date: str = DEFAULT_START_DATE) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out['StepRaw'] = df['step'].astype(int)
    out['HourOfDay'] = (out['StepRaw'] - 1) % 24
    out['StepDay'] = ((out['StepRaw'] - 1) // 24) + 1
    base = datetime.strptime(start_date, '%Y-%m-%d')
    out['DateKey'] = out['StepDay'].apply(
        lambda d: int((base + timedelta(days=int(d) - 1)).strftime('%Y%m%d'))
    )
    out['TimeKey'] = out['HourOfDay']
    out['TypeCode'] = df['type'].astype(str)
    out['IsHighRiskType'] = out['TypeCode'].isin(HIGH_RISK_TYPES).astype(int)
    out['Amount'] = df['amount'].astype(float).round(2)
    out['BandCode'] = out['Amount'].apply(amount_band_code)
    out['NameOrig'] = df['nameOrig'].astype(str)
    out['NameDest'] = df['nameDest'].astype(str)
    out['OrigAccountType'] = out['NameOrig'].str[0]
    out['DestAccountType'] = out['NameDest'].str[0]
    out['OldBalanceOrig'] = df['oldbalanceOrg'].astype(float).round(2)
    out['NewBalanceOrig'] = df['newbalanceOrig'].astype(float).round(2)
    out['OldBalanceDest'] = df['oldbalanceDest'].astype(float).round(2)
    out['NewBalanceDest'] = df['newbalanceDest'].astype(float).round(2)
    out['BalanceDropOrig'] = (out['OldBalanceOrig'] - out['NewBalanceOrig']).round(2)
    out['IsFraud'] = df['isFraud'].astype(int)
    out['IsFlaggedFraud'] = df['isFlaggedFraud'].astype(int)
    return out
