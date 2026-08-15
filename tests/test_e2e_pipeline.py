"""
End-to-end test cho ETL pipeline PaySim.
Test nay KHONG can SQL Server - dung fake connection de xac nhan:
  1. Extract doc CSV dung
  2. Validate tach valid/reject dung
  3. Transform tao dung cac cot phu
  4. Load logic chuan bi dung tham so
  5. Luong extract -> validate -> transform -> (fake) load chay khong loi
"""
import pandas as pd
import os
import sys

# --- Tu xay sample data nho thay vi doc CSV that ---
SAMPLE_DATA = [
    {"step": 1, "type": "TRANSFER", "amount": 181.0, "nameOrig": "C1305486145", "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0, "nameDest": "C553264065", "oldbalanceDest": 0.0, "newbalanceDest": 0.0, "isFraud": 1, "isFlaggedFraud": 0},
    {"step": 1, "type": "PAYMENT", "amount": 9839.64, "nameOrig": "C1231006815", "oldbalanceOrg": 170136.0, "newbalanceOrig": 160296.36, "nameDest": "M1979787155", "oldbalanceDest": 0.0, "newbalanceDest": 0.0, "isFraud": 0, "isFlaggedFraud": 0},
    {"step": 2, "type": "CASH_OUT", "amount": 181.0, "nameOrig": "C840083671", "oldbalanceOrg": 181.0, "newbalanceOrig": 0.0, "nameDest": "C38997010", "oldbalanceDest": 21182.0, "newbalanceDest": 0.0, "isFraud": 1, "isFlaggedFraud": 0},
    {"step": 3, "type": "CASH_IN", "amount": 5000.0, "nameOrig": "C100000001", "oldbalanceOrg": 0.0, "newbalanceOrig": 5000.0, "nameDest": "C200000001", "oldbalanceDest": 50000.0, "newbalanceDest": 55000.0, "isFraud": 0, "isFlaggedFraud": 0},
    {"step": 3, "type": "DEBIT", "amount": 200.0, "nameOrig": "C300000001", "oldbalanceOrg": 1000.0, "newbalanceOrig": 800.0, "nameDest": "C400000001", "oldbalanceDest": 0.0, "newbalanceDest": 200.0, "isFraud": 0, "isFlaggedFraud": 0},
    {"step": 1, "type": "BADTYPE", "amount": -5.0, "nameOrig": "X999", "oldbalanceOrg": 0.0, "newbalanceOrig": 0.0, "nameDest": "Y888", "oldbalanceDest": 0.0, "newbalanceDest": 0.0, "isFraud": 2, "isFlaggedFraud": 3},
]


def test_e2e_extract_validate_transform():
    """Test luong: raw -> validate -> transform khong loi."""
    from src.etl.validate import validate_chunk
    from src.etl.transform import transform_chunk

    df = pd.DataFrame(SAMPLE_DATA)
    assert len(df) == 6, "Sample data phai co 6 dong"

    # Validate
    valid, reject = validate_chunk(df)
    assert len(valid) == 5, f"5 dong hop le, got {len(valid)}"
    assert len(reject) == 1, f"1 dong reject, got {len(reject)}"
    assert "invalid_type" in reject.iloc[0]["RejectReason"]
    assert "negative_amount" in reject.iloc[0]["RejectReason"]

    # Transform
    transformed = transform_chunk(valid)
    assert len(transformed) == 5

    # Kiem tra cac cot phu
    row0 = transformed.iloc[0]
    assert row0["StepRaw"] == 1
    assert row0["HourOfDay"] == 0
    assert row0["StepDay"] == 1
    assert row0["TimeKey"] == 0
    assert row0["TypeCode"] == "TRANSFER"
    assert row0["BandCode"] == "XS"
    assert row0["BalanceDropOrig"] == 181.0
    assert row0["IsFraud"] == 1
    assert row0["NameOrig"] == "C1305486145"
    assert row0["OrigAccountType"] == "C"
    assert row0["DestAccountType"] == "C"

    # Kiem tra merchant detection
    row1 = transformed.iloc[1]
    assert row1["TypeCode"] == "PAYMENT"
    assert row1["DestAccountType"] == "M"  # M1979787155

    # Kiem tra cac loai giao dich khac
    type_codes = set(transformed["TypeCode"].tolist())
    assert type_codes == {"TRANSFER", "PAYMENT", "CASH_OUT", "CASH_IN", "DEBIT"}


def test_e2e_amount_bands_coverage():
    """Kiem tra tat ca 6 amount band duoc map dung."""
    from src.etl.transform import amount_band_code
    assert amount_band_code(500) == "XS"
    assert amount_band_code(1000) == "S"
    assert amount_band_code(5000) == "S"
    assert amount_band_code(10000) == "M"
    assert amount_band_code(50000) == "M"
    assert amount_band_code(100000) == "L"
    assert amount_band_code(500000) == "L"
    assert amount_band_code(1000000) == "XL"
    assert amount_band_code(5000000) == "XL"
    assert amount_band_code(10000000) == "XXL"
    assert amount_band_code(99000000) == "XXL"


def test_e2e_date_time_mapping():
    """Kiem tra step -> DateKey/TimeKey mapping."""
    from src.etl.transform import transform_chunk
    df = pd.DataFrame([
        {"step": 1, "type": "TRANSFER", "amount": 100, "nameOrig": "C1", "oldbalanceOrg": 100, "newbalanceOrig": 0, "nameDest": "C2", "oldbalanceDest": 0, "newbalanceDest": 0, "isFraud": 0, "isFlaggedFraud": 0},
        {"step": 25, "type": "TRANSFER", "amount": 100, "nameOrig": "C1", "oldbalanceOrg": 100, "newbalanceOrig": 0, "nameDest": "C2", "oldbalanceDest": 0, "newbalanceDest": 0, "isFraud": 0, "isFlaggedFraud": 0},
        {"step": 49, "type": "TRANSFER", "amount": 100, "nameOrig": "C1", "oldbalanceOrg": 100, "newbalanceOrig": 0, "nameDest": "C2", "oldbalanceDest": 0, "newbalanceDest": 0, "isFraud": 0, "isFlaggedFraud": 0},
        {"step": 743, "type": "TRANSFER", "amount": 100, "nameOrig": "C1", "oldbalanceOrg": 100, "newbalanceOrig": 0, "nameDest": "C2", "oldbalanceDest": 0, "newbalanceDest": 0, "isFraud": 0, "isFlaggedFraud": 0},
    ])
    out = transform_chunk(df)
    # step=1: day1, hour0
    assert out.iloc[0]["StepDay"] == 1
    assert out.iloc[0]["HourOfDay"] == 0
    assert out.iloc[0]["DateKey"] == 20230101

    # step=25: day2, hour0
    assert out.iloc[1]["StepDay"] == 2
    assert out.iloc[1]["HourOfDay"] == 0
    assert out.iloc[1]["DateKey"] == 20230102

    # step=49: day3, hour0
    assert out.iloc[2]["StepDay"] == 3
    assert out.iloc[2]["HourOfDay"] == 0
    assert out.iloc[2]["DateKey"] == 20230103

    # step=743: day31, hour22
    assert out.iloc[3]["StepDay"] == 31
    assert out.iloc[3]["HourOfDay"] == 22


def test_e2e_fraud_counts_after_validate():
    """Dam bao fraud count khong bi mat sau validate."""
    from src.etl.validate import validate_chunk
    df = pd.DataFrame(SAMPLE_DATA)
    valid, _ = validate_chunk(df)
    fraud_count = int((valid["isFraud"] == 1).sum())
    assert fraud_count == 2, f"Phai co 2 fraud trong valid, got {fraud_count}"


def test_e2e_reconciliation_logic():
    """Test reconciliation logic pass va fail."""
    from src.etl.reconciliation import reconcile

    # Mock connection
    class FakeConn:
        def __init__(self, rows, amount, fraud):
            self._r = rows; self._a = amount; self._f = fraud
        def cursor(self):
            return FakeCur(self)

    class FakeCur:
        def __init__(self, c):
            self._c = c; self._sql = None
        def execute(self, sql, p=()):
            self._sql = sql
        def fetchall(self):
            if "BatchFacts" in self._sql:
                return [(self._c._r, self._c._a, self._c._f)]
            if "duplicate_grains" in self._sql or "WHERE d.DateKey IS NULL" in self._sql:
                return [(0,)]
            return []
        def close(self):
            pass

    # PASS case
    r = reconcile(FakeConn(100, 5000.0, 3), 1, 100, 5000.0, 3)
    assert r["status"] == "PASS"
    assert r["row_count_match"] is True
    assert r["fraud_match"] is True

    # FAIL case
    r2 = reconcile(FakeConn(99, 5000.0, 3), 1, 100, 5000.0, 3)
    assert r2["status"] == "FAIL"
    assert r2["row_count_match"] is False
