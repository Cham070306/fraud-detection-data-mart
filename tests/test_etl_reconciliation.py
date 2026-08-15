from src.etl.reconciliation import reconcile


class FakeConn:
    def __init__(self, fact_rows, fact_amount, fact_fraud):
        self._fact_rows = fact_rows
        self._fact_amount = fact_amount
        self._fact_fraud = fact_fraud

    def cursor(self):
        return FakeCursor(self)


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._sql = None

    def execute(self, sql, params=()):
        self._sql = sql
        self._params = params
        return self

    def fetchall(self):
        sql = self._sql
        if 'BatchFacts' in sql:
            return [(self._conn._fact_rows, self._conn._fact_amount,
                     self._conn._fact_fraud)]
        if 'duplicate_grains' in sql or 'WHERE d.DateKey IS NULL' in sql:
            return [(0,)]
        return []

    def close(self):
        pass


def test_reconcile_pass():
    conn = FakeConn(fact_rows=10, fact_amount=100.0, fact_fraud=2)
    result = reconcile(conn, batch_id=1, expected_source_rows=10, expected_amount_sum=100.0, expected_fraud_count=2)
    assert result['status'] == 'PASS'
    assert result['row_count_match'] is True
    assert result['fraud_match'] is True


def test_reconcile_fail_on_row_mismatch():
    conn = FakeConn(fact_rows=9, fact_amount=100.0, fact_fraud=2)
    result = reconcile(conn, batch_id=1, expected_source_rows=10, expected_amount_sum=100.0, expected_fraud_count=2)
    assert result['status'] == 'FAIL'
    assert result['row_count_match'] is False


def test_reconcile_fail_on_amount_mismatch():
    conn = FakeConn(fact_rows=10, fact_amount=99.0, fact_fraud=2)
    result = reconcile(conn, batch_id=1, expected_source_rows=10,
                       expected_amount_sum=100.0, expected_fraud_count=2)
    assert result['status'] == 'FAIL'
    assert result['amount_match'] is False


def test_idempotent_rerun_with_zero_inserts_passes():
    result = reconcile(FakeConn(10, 100.0, 2), 2, 10, 100.0, 2,
                       inserted_rows=0)
    assert result['status'] == 'PASS'
    assert result['inserted_rows'] == 0
    assert result['existing_rows'] == 10
