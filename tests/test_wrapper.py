"""Tests for TableWrapper core methods."""

from __future__ import annotations

import json

import pytest
from helpers import make_table

from behave_tables import ColumnMismatchError, wrap


class TestAsDicts:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.as_dicts() == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_table(self):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        assert wt.as_dicts() == []

    def test_single_row(self):
        table = make_table(["x"], [["1"]])
        wt = wrap(table)
        assert wt.as_dicts() == [{"x": "1"}]

    def test_single_column(self):
        table = make_table(["only"], [["a"], ["b"], ["c"]])
        wt = wrap(table)
        assert wt.as_dicts() == [{"only": "a"}, {"only": "b"}, {"only": "c"}]

    def test_returns_copy(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        dicts = wt.as_dicts()
        dicts[0]["name"] = "modified"
        assert wt.as_dicts()[0]["name"] == "Alice"


class TestColumn:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.column("name") == ["Alice", "Bob"]
        assert wt.column("age") == ["30", "25"]

    def test_missing_column(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.column("email")

    def test_empty_table(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.column("name") == []


class TestFindRow:
    def test_single_filter(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.find_row(name="Alice") == {"name": "Alice", "age": "30"}

    def test_multiple_filters(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.find_row(name="Alice", age="30") == {"name": "Alice", "age": "30"}

    def test_no_match(self):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        assert wt.find_row(name="Charlie") is None

    def test_no_filters_returns_first(self):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        assert wt.find_row() == {"name": "Alice"}

    def test_no_filters_empty_table(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.find_row() is None

    def test_returns_copy(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt.find_row(name="Alice")
        row["name"] = "modified"
        assert wt.find_row(name="Alice") is not None


class TestValidateColumns:
    def test_all_present(self):
        table = make_table(["name", "age", "email"], [])
        wt = wrap(table)
        wt.validate_columns("name", "age")

    def test_missing(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError, match="missing columns"):
            wt.validate_columns("name", "email", "phone")

    def test_empty_expected(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        wt.validate_columns()


class TestTranspose:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert transposed.headers == ["_column", "0", "1"]
        dicts = transposed.as_dicts()
        assert dicts[0] == {"_column": "name", "0": "Alice", "1": "Bob"}
        assert dicts[1] == {"_column": "age", "0": "30", "1": "25"}

    def test_original_unchanged(self):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert wt.as_dicts() == [{"name": "Alice", "age": "30"}]
        assert transposed.headers != wt.headers

    def test_empty_table(self):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        transposed = wt.transpose()
        assert len(transposed) == 2
        assert transposed.headers == ["_column"]


class TestToCsv:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[0] == "name,age"
        assert lines[1] == "Alice,30"
        assert lines[2] == "Bob,25"

    def test_empty_table(self):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        csv_str = wt.to_csv()
        assert csv_str == "name,age"

    def test_missing_values_filled_with_empty(self):
        from behave_tables._mock import MockTable

        mock = MockTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice"}],
        )
        wt = wrap(mock)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[1] == "Alice,"

    def test_extra_keys_ignored(self):
        from behave_tables._mock import MockTable

        mock = MockTable(
            headings=["name"],
            rows_data=[{"name": "Alice", "extra": "ignored"}],
        )
        wt = wrap(mock)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[1] == "Alice"


class TestToJson:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        json_str = wt.to_json()
        parsed = json.loads(json_str)
        assert parsed == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_table(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        json_str = wt.to_json()
        assert json.loads(json_str) == []

    def test_indent_zero(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json(indent=0)
        assert json.loads(json_str) == [{"name": "Alice"}]

    def test_indent_none(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json(indent=None)
        assert "\n" not in json_str
        assert json.loads(json_str) == [{"name": "Alice"}]


class TestIteration:
    def test_iter(self):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        rows = [r for r in wt]
        assert rows == [{"name": "Alice"}, {"name": "Bob"}]

    def test_iter_returns_copies(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        for row in wt:
            row["name"] = "modified"
        assert wt.as_dicts()[0]["name"] == "Alice"

    def test_getitem(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt[0] == {"name": "Alice", "age": "30"}
        assert wt[1] == {"name": "Bob", "age": "25"}

    def test_getitem_returns_copy(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt[0]
        row["name"] = "modified"
        assert wt[0]["name"] == "Alice"

    def test_getitem_index_error(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(IndexError):
            wt[5]

    def test_len(self):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        assert len(wt) == 3

    def test_len_empty(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert len(wt) == 0


class TestHeaders:
    def test_basic(self):
        table = make_table(["name", "age", "email"], [])
        wt = wrap(table)
        assert wt.headers == ["name", "age", "email"]

    def test_returns_copy(self):
        table = make_table(["name"], [])
        wt = wrap(table)
        headers = wt.headers
        headers.append("extra")
        assert wt.headers == ["name"]


class TestExtractRows:
    def test_row_with_getitem_no_as_dict(self):
        class SimpleRow:
            def __init__(self, data):
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

        class SimpleTable:
            headings = ["name", "age"]

            @property
            def rows(self):
                return [SimpleRow({"name": "Alice", "age": "30"})]

        wt = wrap(SimpleTable())
        assert wt.as_dicts() == [{"name": "Alice", "age": "30"}]

    def test_unsupported_row_type(self):
        class BadRow:
            pass

        class BadTable:
            headings = ["name"]

            @property
            def rows(self):
                return [BadRow()]

        with pytest.raises(TypeError, match="Unsupported row type"):
            wrap(BadTable())


class TestRepr:
    def test_repr(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        r = repr(wt)
        assert "TableWrapper" in r
        assert "name" in r
        assert "rows=2" in r
