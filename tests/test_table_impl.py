"""Tests for internal _table_impl module."""

from __future__ import annotations

from behave_tables._table_impl import SimpleRow, SimpleTable


class TestSimpleRow:
    def test_as_dict(self):
        row = SimpleRow({"name": "Alice", "age": "30"})
        assert row.as_dict() == {"name": "Alice", "age": "30"}

    def test_as_dict_returns_copy(self):
        row = SimpleRow({"name": "Alice"})
        d = row.as_dict()
        d["name"] = "modified"
        assert row.as_dict()["name"] == "Alice"

    def test_getitem(self):
        row = SimpleRow({"name": "Alice", "age": "30"})
        assert row["name"] == "Alice"
        assert row["age"] == "30"


class TestSimpleTable:
    def test_rows(self):
        table = SimpleTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice", "age": "30"}],
        )
        rows = table.rows
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"

    def test_empty_rows(self):
        table = SimpleTable(headings=["name"])
        assert table.rows == []
