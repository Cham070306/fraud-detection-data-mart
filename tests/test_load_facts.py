import pandas as pd
import pytest

from src.etl.load_facts import load_fact_transaction
from src.etl.transform import transform_chunk


RAW = pd.DataFrame([{
    "step": 1, "type": "TRANSFER", "amount": 10.0,
    "nameOrig": "C1", "oldbalanceOrg": 10.0, "newbalanceOrig": 0.0,
    "nameDest": "C2", "oldbalanceDest": 0.0, "newbalanceDest": 10.0,
    "isFraud": 0, "isFlaggedFraud": 0,
}])
LOOKUPS = {"account": {"C1": 1, "C2": 2}, "type": {"TRANSFER": 1}, "band": {"XS": 1}}


class Cursor:
    def __init__(self, conn):
        self.conn, self.rows, self.result, self.closed = conn, [], [], False
    def execute(self, sql, params=()):
        if "DROP TABLE IF EXISTS #FactInput" in sql:
            self.conn.fact_temp_exists = False
            self.rows = []
        if "CREATE TABLE #FactInput" in sql:
            if self.conn.fact_temp_exists:
                raise RuntimeError("#FactInput already exists")
            self.conn.fact_temp_exists = True
        if self.conn.fail and "INSERT INTO fact.FactTransaction" in sql:
            raise RuntimeError("injected failure")
        if "INSERT INTO fact.FactTransaction" in sql:
            new = [row for row in self.rows if row not in self.conn.persisted]
            self.conn.persisted.update(new)
            self.result = [(len(new),)]
        return self
    def executemany(self, sql, rows):
        assert sql.count("?") == len(next(iter(rows)))
        self.rows = list(rows)
    def fetchone(self): return self.result[0]
    def close(self): self.closed = True


class Conn:
    def __init__(self, fail=False):
        self.persisted, self.fail = set(), fail
        self.fact_temp_exists, self.cursors = False, []
        self.commits = self.rollbacks = 0
    def cursor(self):
        cur = Cursor(self)
        self.cursors.append(cur)
        return cur
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def test_second_fact_load_is_idempotent():
    conn = Conn()
    transformed = transform_chunk(RAW)
    assert load_fact_transaction(conn, transformed, LOOKUPS, 1) == 1
    assert load_fact_transaction(conn, transformed, LOOKUPS, 2) == 0
    assert len(conn.persisted) == 1
    assert conn.fact_temp_exists is False
    assert all(cursor.closed for cursor in conn.cursors)


def test_fact_load_rolls_back_on_error():
    conn = Conn(fail=True)
    with pytest.raises(RuntimeError, match="injected failure"):
        load_fact_transaction(conn, transform_chunk(RAW), LOOKUPS, 1)
    assert conn.commits == 0
    assert conn.rollbacks == 1
