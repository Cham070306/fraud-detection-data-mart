from src.etl.load_dimensions import chunked, ensure_accounts, normalize_account_ids


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn
        self.accounts = conn.accounts
        self.input = []
        self.result = []
        self.calls = []
        self.closed = False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))
        if "DROP TABLE IF EXISTS #AccountInput" in sql:
            self.conn.account_temp_exists = False
            self.input = []
        if "CREATE TABLE #AccountInput" in sql:
            if self.conn.account_temp_exists:
                raise RuntimeError("#AccountInput already exists")
            self.conn.account_temp_exists = True
        if "INSERT INTO dim.DimAccount" in sql:
            inserted = 0
            for account_id in self.input:
                if account_id not in self.accounts:
                    self.accounts[account_id] = len(self.accounts) + 1
                    inserted += 1
            self.result = [(inserted,)]
        elif "JOIN #AccountInput" in sql and "SELECT d.AccountID" in sql:
            self.result = [(value, self.accounts[value]) for value in self.input]
        return self

    def executemany(self, sql, rows):
        rows = list(rows)
        self.calls.append((sql, rows))
        assert sql.count("?") == 1
        assert all(len(row) == 1 for row in rows)
        self.input.extend(row[0] for row in rows)

    def fetchone(self): return self.result[0]
    def fetchall(self): return self.result
    def close(self): self.closed = True


class FakeConn:
    def __init__(self, existing=()):
        self.accounts = {value: index + 1 for index, value in enumerate(existing)}
        self.account_temp_exists = False
        self.cursors = []
        self.commits = 0
        self.rollbacks = 0
    def cursor(self):
        cur = FakeCursor(self)
        self.cursors.append(cur)
        return cur
    def commit(self): self.commits += 1
    def rollback(self): self.rollbacks += 1


def test_normalize_empty_none_duplicates_and_nested_values():
    values = [None, "", "  ", "C1", ["C1", " M2 "], 123, "X3", "Cabc"]
    assert normalize_account_ids(values) == ["C1", "M2"]
    assert ensure_accounts(FakeConn(), []) == {}


def test_chunked_more_than_batch_size():
    assert list(chunked(list(range(5)), 2)) == [[0, 1], [2, 3], [4]]


def test_large_account_input_uses_bounded_single_marker_batches():
    values = [f"C{i}" for i in range(5000)]
    conn = FakeConn()
    mapping = ensure_accounts(conn, values, batch_size=1000)
    inserts = [call for call in conn.cursors[0].calls if "VALUES (?)" in call[0]]
    assert len(mapping) == 5000
    assert len(inserts) == 5
    assert max(len(rows) for _, rows in inserts) == 1000


def test_existing_account_is_not_inserted_or_rekeyed():
    conn = FakeConn(existing=["C1"])
    first_key = conn.accounts["C1"]
    mapping = ensure_accounts(conn, ["C1", "C2", "C2"])
    assert mapping["C1"] == first_key
    assert len(conn.accounts) == 2


def test_two_account_chunks_share_connection_without_temp_collision():
    conn = FakeConn()
    assert ensure_accounts(conn, ["C1"]) == {"C1": 1}
    assert ensure_accounts(conn, ["C2"]) == {"C2": 2}
    assert conn.account_temp_exists is False
    assert all(cursor.closed for cursor in conn.cursors)


def test_missing_mapping_rolls_back_and_raises():
    conn = FakeConn()
    original_cursor = conn.cursor

    def cursor_without_mapping():
        cur = original_cursor()
        original_execute = cur.execute
        def execute(sql, params=()):
            result = original_execute(sql, params)
            if "SELECT d.AccountID" in sql:
                cur.result = []
            return result
        cur.execute = execute
        return cur

    conn.cursor = cursor_without_mapping
    import pytest
    with pytest.raises(RuntimeError, match="lookup missing"):
        ensure_accounts(conn, ["C1"])
    assert conn.rollbacks == 1
