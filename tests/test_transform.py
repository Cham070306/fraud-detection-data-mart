import pandas as pd
from src.etl.transform import transform_chunk


def test_transform_chunk_generates_expected_fields():
    df = pd.DataFrame([
        {
            'step': 1,
            'type': 'TRANSFER',
            'amount': 181.0,
            'nameOrig': 'C123',
            'oldbalanceOrg': 181.0,
            'newbalanceOrig': 0.0,
            'nameDest': 'C456',
            'oldbalanceDest': 0.0,
            'newbalanceDest': 0.0,
            'isFraud': 1,
            'isFlaggedFraud': 0,
        }
    ])
    out = transform_chunk(df)
    row = out.iloc[0]
    assert row['StepRaw'] == 1
    assert row['HourOfDay'] == 0
    assert row['StepDay'] == 1
    assert row['TimeKey'] == 0
    assert row['TypeCode'] == 'TRANSFER'
    assert row['BandCode'] == 'XS'
    assert row['BalanceDropOrig'] == 181.0
    assert row['IsFraud'] == 1
