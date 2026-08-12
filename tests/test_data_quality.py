import pandas as pd
from src.etl.validate import validate_chunk


def test_validate_chunk_splits_invalid_rows():
    df = pd.DataFrame([
        {'step': 1, 'type': 'TRANSFER', 'amount': 10.0, 'nameOrig': 'C1', 'oldbalanceOrg': 10.0, 'newbalanceOrig': 0.0, 'nameDest': 'C2', 'oldbalanceDest': 0.0, 'newbalanceDest': 0.0, 'isFraud': 1, 'isFlaggedFraud': 0},
        {'step': 1, 'type': 'BADTYPE', 'amount': -1.0, 'nameOrig': 'X1', 'oldbalanceOrg': 0.0, 'newbalanceOrig': 0.0, 'nameDest': 'Y2', 'oldbalanceDest': 0.0, 'newbalanceDest': 0.0, 'isFraud': 2, 'isFlaggedFraud': 3},
    ])
    valid, reject = validate_chunk(df)
    assert len(valid) == 1
    assert len(reject) == 1
    assert 'invalid_type' in reject.iloc[0]['RejectReason']
    assert 'negative_amount' in reject.iloc[0]['RejectReason']
