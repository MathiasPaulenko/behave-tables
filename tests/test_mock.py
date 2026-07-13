"""Tests for internal _mock module."""

from __future__ import annotations

from behave_tables._mock import MockRow, MockTable


class TestMockRow:
    def test_as_dict(self):
        row = MockRow({"name": "Alice", "age": "30"})
        assert row.as_dict() == {"name": "Alice", "age": "30"}

    def test_as_dict_returns_copy(self):
        row = MockRow({"name": "Alice"})
        d = row.as_dict()
        d["name"] = "modified"
        assert row.as_dict()["name"] == "Alice"

    def test_getitem(self):
        row = MockRow({"name": "Alice", "age": "30"})
        assert row["name"] == "Alice"
        assert row["age"] == "30"


class TestMockTable:
    def test_rows(self):
        table = MockTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice", "age": "30"}],
        )
        rows = table.rows
        assert len(rows) == 1
        assert rows[0]["name"] == "Alice"

    def test_empty_rows(self):
        table = MockTable(headings=["name"])
        assert table.rows == []
