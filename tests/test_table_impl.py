"""Tests for internal _table_impl module."""

from __future__ import annotations

import pytest

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


class TestSimpleRowEdgeCases:
    def test_getitem_missing_key_raises(self):
        row = SimpleRow({"name": "Alice"})
        with pytest.raises(KeyError):
            row["nonexistent"]

    def test_as_dict_empty(self):
        row = SimpleRow({})
        assert row.as_dict() == {}

    def test_as_dict_modification_does_not_affect_row(self):
        data = {"name": "Alice"}
        row = SimpleRow(data)
        d = row.as_dict()
        d["name"] = "modified"
        assert row["name"] == "Alice"

    def test_getitem_returns_value(self):
        row = SimpleRow({"key": "value"})
        assert row["key"] == "value"


class TestSimpleTableEdgeCases:
    def test_rows_returns_new_instances_each_call(self):
        table = SimpleTable(
            headings=["name"],
            rows_data=[{"name": "Alice"}],
        )
        r1 = table.rows
        r2 = table.rows
        assert r1[0] is not r2[0]

    def test_default_rows_data_is_empty(self):
        table = SimpleTable(headings=["name"])
        assert table.rows_data == []

    def test_multiple_rows(self):
        table = SimpleTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}],
        )
        rows = table.rows
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[1]["name"] == "Bob"

    def test_rows_with_missing_keys_in_data(self):
        table = SimpleTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice"}],
        )
        rows = table.rows
        assert rows[0]["name"] == "Alice"

    def test_empty_headings(self):
        table = SimpleTable(headings=[], rows_data=[{}])
        rows = table.rows
        assert len(rows) == 1
