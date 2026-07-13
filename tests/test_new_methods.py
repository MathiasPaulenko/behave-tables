"""Tests for new TableWrapper methods.

Covers: select, drop, rename_columns, sort, unique, distinct,
count, first, last, to_jsonl, from_csv, from_json.
"""

from __future__ import annotations

import json

import pytest

from behave_tables import TableWrapper, wrap


class TestSelect:
    def test_basic(self, make_table):
        table = make_table(["name", "age", "city"], [["Alice", "30", "NYC"]])
        wt = wrap(table)
        result = wt.select("name", "city")
        assert result.headers == ["name", "city"]
        assert result.as_dicts() == [{"name": "Alice", "city": "NYC"}]

    def test_reorders_columns(self, make_table):
        table = make_table(["a", "b", "c"], [["1", "2", "3"]])
        wt = wrap(table)
        result = wt.select("c", "a")
        assert result.headers == ["c", "a"]
        assert result.as_dicts() == [{"c": "3", "a": "1"}]

    def test_single_column(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.select("name")
        assert result.headers == ["name"]
        assert result.as_dicts() == [{"name": "Alice"}]

    def test_all_columns(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.select("name", "age")
        assert result.headers == ["name", "age"]

    def test_missing_column_raises(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.select("name", "email")

    def test_empty_selection(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        result = wt.select()
        assert result.headers == []
        assert result.as_dicts() == [{}]

    def test_preserves_row_count(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        result = wt.select("name")
        assert len(result) == 2

    def test_original_unchanged(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        wt.select("name")
        assert wt.headers == ["name", "age"]


class TestDrop:
    def test_basic(self, make_table):
        table = make_table(["name", "age", "city"], [["Alice", "30", "NYC"]])
        wt = wrap(table)
        result = wt.drop("age")
        assert result.headers == ["name", "city"]
        assert result.as_dicts() == [{"name": "Alice", "city": "NYC"}]

    def test_multiple_columns(self, make_table):
        table = make_table(["a", "b", "c", "d"], [["1", "2", "3", "4"]])
        wt = wrap(table)
        result = wt.drop("b", "d")
        assert result.headers == ["a", "c"]

    def test_drop_all(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.drop("name", "age")
        assert result.headers == []
        assert result.as_dicts() == [{}]

    def test_missing_column_raises(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.drop("email")

    def test_original_unchanged(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        wt.drop("age")
        assert wt.headers == ["name", "age"]


class TestRenameColumns:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.rename_columns({"name": "full_name"})
        assert result.headers == ["full_name", "age"]
        assert result.as_dicts() == [{"full_name": "Alice", "age": "30"}]

    def test_rename_all(self, make_table):
        table = make_table(["a", "b"], [["1", "2"]])
        wt = wrap(table)
        result = wt.rename_columns({"a": "x", "b": "y"})
        assert result.headers == ["x", "y"]
        assert result.as_dicts() == [{"x": "1", "y": "2"}]

    def test_rename_partial(self, make_table):
        table = make_table(["a", "b", "c"], [["1", "2", "3"]])
        wt = wrap(table)
        result = wt.rename_columns({"b": "y"})
        assert result.headers == ["a", "y", "c"]

    def test_missing_column_raises(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.rename_columns({"email": "e"})

    def test_empty_mapping(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        result = wt.rename_columns({})
        assert result.headers == ["name"]

    def test_original_unchanged(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        wt.rename_columns({"name": "x"})
        assert wt.headers == ["name"]


class TestSort:
    def test_by_column_ascending(self, make_table):
        table = make_table(["name", "age"], [["Charlie", "25"], ["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        result = wt.sort("name")
        assert [r["name"] for r in result] == ["Alice", "Bob", "Charlie"]

    def test_by_column_descending(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        result = wt.sort("age", reverse=True)
        assert [r["name"] for r in result] == ["Alice", "Bob"]

    def test_by_callable(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        result = wt.sort(lambda row: len(row["name"]))
        assert [r["name"] for r in result] == ["Bob", "Alice"]

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        result = wt.sort("name")
        assert len(result) == 0

    def test_single_row(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        result = wt.sort("name")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_preserves_headers(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.sort("name")
        assert result.headers == ["name", "age"]

    def test_original_unchanged(self, make_table):
        table = make_table(["name"], [["Bob"], ["Alice"]])
        wt = wrap(table)
        wt.sort("name")
        assert wt[0]["name"] == "Bob"


class TestUnique:
    def test_basic(self, make_table):
        table = make_table(["name", "city"], [["Alice", "NYC"], ["Bob", "NYC"], ["Charlie", "LA"]])
        wt = wrap(table)
        assert wt.unique("city") == ["NYC", "LA"]

    def test_all_unique(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        assert wt.unique("name") == ["Alice", "Bob", "Charlie"]

    def test_all_same(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "30"]])
        wt = wrap(table)
        assert wt.unique("age") == ["30"]

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.unique("name") == []

    def test_missing_column_raises(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.unique("email")


class TestDistinct:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        result = wt.distinct()
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}
        assert result[1] == {"name": "Bob", "age": "25"}

    def test_no_duplicates(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        result = wt.distinct()
        assert len(result) == 2

    def test_all_duplicates(self, make_table):
        table = make_table(["name"], [["Alice"], ["Alice"], ["Alice"]])
        wt = wrap(table)
        result = wt.distinct()
        assert len(result) == 1
        assert result[0] == {"name": "Alice"}

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        result = wt.distinct()
        assert len(result) == 0

    def test_preserves_headers(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        result = wt.distinct()
        assert result.headers == ["name", "age"]

    def test_original_unchanged(self, make_table):
        table = make_table(["name"], [["Alice"], ["Alice"]])
        wt = wrap(table)
        wt.distinct()
        assert len(wt) == 2


class TestCount:
    def test_no_filters(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        assert wt.count() == 3

    def test_single_filter(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "30"], ["Charlie", "25"]])
        wt = wrap(table)
        assert wt.count(age="30") == 2

    def test_multiple_filters(self, make_table):
        table = make_table(
            ["name", "age", "city"],
            [["Alice", "30", "NYC"], ["Bob", "30", "NYC"], ["Charlie", "30", "LA"]],
        )
        wt = wrap(table)
        assert wt.count(age="30", city="NYC") == 2

    def test_no_match(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.count(name="Charlie") == 0

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.count() == 0
        assert wt.count(name="Alice") == 0

    def test_nonexistent_column(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.count(nonexistent="value") == 0


class TestFirstLast:
    def test_first(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        assert wt.first() == {"name": "Alice"}

    def test_last(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        assert wt.last() == {"name": "Bob"}

    def test_first_empty(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.first() is None

    def test_last_empty(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.last() is None

    def test_first_single_row(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.first() == {"name": "Alice"}
        assert wt.last() == {"name": "Alice"}

    def test_first_returns_copy(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt.first()
        row["name"] = "modified"
        assert wt.first()["name"] == "Alice"

    def test_last_returns_copy(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt.last()
        row["name"] = "modified"
        assert wt.last()["name"] == "Alice"


class TestToJsonl:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        jsonl = wt.to_jsonl()
        lines = jsonl.split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"name": "Alice", "age": "30"}
        assert json.loads(lines[1]) == {"name": "Bob", "age": "25"}

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.to_jsonl() == ""

    def test_single_row(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        jsonl = wt.to_jsonl()
        assert json.loads(jsonl) == {"name": "Alice"}

    def test_no_trailing_newline(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert not wt.to_jsonl().endswith("\n")

    def test_unicode(self, make_table):
        table = make_table(["name"], [["café"]])
        wt = wrap(table)
        jsonl = wt.to_jsonl()
        assert "café" in jsonl


class TestFromCsv:
    def test_basic(self):
        csv_str = "name,age\nAlice,30\nBob,25\n"
        wt = TableWrapper.from_csv(csv_str)
        assert wt.headers == ["name", "age"]
        assert wt.as_dicts() == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_custom_delimiter(self):
        csv_str = "name;age\nAlice;30\n"
        wt = TableWrapper.from_csv(csv_str, delimiter=";")
        assert wt.headers == ["name", "age"]
        assert wt[0] == {"name": "Alice", "age": "30"}

    def test_empty_csv(self):
        csv_str = "name,age\n"
        wt = TableWrapper.from_csv(csv_str)
        assert wt.headers == ["name", "age"]
        assert len(wt) == 0

    def test_round_trip(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        csv_str = wt.to_csv()
        restored = TableWrapper.from_csv(csv_str)
        assert restored.headers == wt.headers
        assert restored.as_dicts() == wt.as_dicts()

    def test_single_column(self):
        csv_str = "name\nAlice\nBob\n"
        wt = TableWrapper.from_csv(csv_str)
        assert wt.headers == ["name"]
        assert len(wt) == 2


class TestFromJson:
    def test_basic(self):
        json_str = '[{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]'
        wt = TableWrapper.from_json(json_str)
        assert wt.headers == ["name", "age"]
        assert wt.as_dicts() == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_list(self):
        wt = TableWrapper.from_json("[]")
        assert wt.headers == []
        assert len(wt) == 0

    def test_single_row(self):
        json_str = '[{"name": "Alice"}]'
        wt = TableWrapper.from_json(json_str)
        assert len(wt) == 1
        assert wt[0] == {"name": "Alice"}

    def test_round_trip(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        json_str = wt.to_json()
        restored = TableWrapper.from_json(json_str)
        assert restored.headers == wt.headers
        assert restored.as_dicts() == wt.as_dicts()

    def test_heterogeneous_keys(self):
        json_str = '[{"a": "1", "b": "2"}, {"a": "1", "c": "3"}]'
        wt = TableWrapper.from_json(json_str)
        assert wt.headers == ["a", "b", "c"]
        assert wt[0] == {"a": "1", "b": "2"}
        assert wt[1] == {"a": "1", "c": "3"}

    def test_round_trip_jsonl(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        jsonl = wt.to_jsonl()
        lines = jsonl.split("\n")
        restored = TableWrapper.from_json("[" + ",".join(lines) + "]")
        assert restored.headers == wt.headers
        assert restored.as_dicts() == wt.as_dicts()
