"""Tests for TableWrapper core methods."""

from __future__ import annotations

import json

import pytest

from behave_tables import ColumnMismatchError, wrap


class TestAsDicts:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.as_dicts() == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_table(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        assert wt.as_dicts() == []

    def test_single_row(self, make_table):
        table = make_table(["x"], [["1"]])
        wt = wrap(table)
        assert wt.as_dicts() == [{"x": "1"}]

    def test_single_column(self, make_table):
        table = make_table(["only"], [["a"], ["b"], ["c"]])
        wt = wrap(table)
        assert wt.as_dicts() == [{"only": "a"}, {"only": "b"}, {"only": "c"}]

    def test_returns_copy(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        dicts = wt.as_dicts()
        dicts[0]["name"] = "modified"
        assert wt.as_dicts()[0]["name"] == "Alice"


class TestColumn:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.column("name") == ["Alice", "Bob"]
        assert wt.column("age") == ["30", "25"]

    def test_missing_column(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(KeyError, match="not found"):
            wt.column("email")

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.column("name") == []


class TestFindRow:
    def test_single_filter(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.find_row(name="Alice") == {"name": "Alice", "age": "30"}

    def test_multiple_filters(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.find_row(name="Alice", age="30") == {"name": "Alice", "age": "30"}

    def test_no_match(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        assert wt.find_row(name="Charlie") is None

    def test_no_filters_returns_first(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        assert wt.find_row() == {"name": "Alice"}

    def test_no_filters_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.find_row() is None

    def test_returns_copy(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt.find_row(name="Alice")
        row["name"] = "modified"
        assert wt.find_row(name="Alice") is not None


class TestFindAllRows:
    def test_single_filter(self, make_table):
        table = make_table(
            ["name", "age"],
            [["Alice", "30"], ["Bob", "30"], ["Charlie", "25"]],
        )
        wt = wrap(table)
        result = wt.find_all_rows(age="30")
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}
        assert result[1] == {"name": "Bob", "age": "30"}

    def test_multiple_filters(self, make_table):
        table = make_table(
            ["name", "age", "city"],
            [["Alice", "30", "NYC"], ["Bob", "30", "NYC"], ["Charlie", "30", "LA"]],
        )
        wt = wrap(table)
        result = wt.find_all_rows(age="30", city="NYC")
        assert len(result) == 2

    def test_no_match(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.find_all_rows(name="Charlie") == []

    def test_no_filters_returns_all(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        result = wt.find_all_rows()
        assert len(result) == 2

    def test_returns_copies(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        rows = wt.find_all_rows()
        rows[0]["name"] = "modified"
        assert wt.find_all_rows()[0]["name"] == "Alice"


class TestValidateColumns:
    def test_all_present(self, make_table):
        table = make_table(["name", "age", "email"], [])
        wt = wrap(table)
        wt.validate_columns("name", "age")

    def test_missing(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError, match="missing columns"):
            wt.validate_columns("name", "email", "phone")

    def test_empty_expected(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        wt.validate_columns()

    def test_strict_detects_extra(self, make_table):
        table = make_table(["name", "age", "extra"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError, match="unexpected columns"):
            wt.validate_columns("name", "age", strict=True)

    def test_strict_no_extra(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        wt.validate_columns("name", "age", strict=True)

    def test_strict_missing_and_extra(self, make_table):
        table = make_table(["name", "extra"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError) as exc_info:
            wt.validate_columns("name", "age", strict=True)
        assert "age" in exc_info.value.missing
        assert "extra" in exc_info.value.extra


class TestTranspose:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert transposed.headers == ["_column", "0", "1"]
        dicts = transposed.as_dicts()
        assert dicts[0] == {"_column": "name", "0": "Alice", "1": "Bob"}
        assert dicts[1] == {"_column": "age", "0": "30", "1": "25"}

    def test_original_unchanged(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert wt.as_dicts() == [{"name": "Alice", "age": "30"}]
        assert transposed.headers != wt.headers

    def test_empty_table(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        transposed = wt.transpose()
        assert len(transposed) == 2
        assert transposed.headers == ["_column"]


class TestToCsv:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[0] == "name,age"
        assert lines[1] == "Alice,30"
        assert lines[2] == "Bob,25"

    def test_empty_table(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        csv_str = wt.to_csv()
        assert csv_str == "name,age"

    def test_missing_values_filled_with_empty(self, make_table):
        from behave_tables._table_impl import SimpleTable

        mock = SimpleTable(
            headings=["name", "age"],
            rows_data=[{"name": "Alice"}],
        )
        wt = wrap(mock)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[1] == "Alice,"

    def test_extra_keys_ignored(self, make_table):
        from behave_tables._table_impl import SimpleTable

        mock = SimpleTable(
            headings=["name"],
            rows_data=[{"name": "Alice", "extra": "ignored"}],
        )
        wt = wrap(mock)
        csv_str = wt.to_csv()
        lines = csv_str.split("\n")
        assert lines[1] == "Alice"

    def test_custom_delimiter(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        csv_str = wt.to_csv(delimiter=";")
        lines = csv_str.split("\n")
        assert lines[0] == "name;age"
        assert lines[1] == "Alice;30"

    def test_quoting_all(self, make_table):
        import csv as csv_module

        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        csv_str = wt.to_csv(quoting=csv_module.QUOTE_ALL)
        lines = csv_str.split("\n")
        assert lines[0] == '"name","age"'
        assert lines[1] == '"Alice","30"'


class TestToJson:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        json_str = wt.to_json()
        parsed = json.loads(json_str)
        assert parsed == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]

    def test_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        json_str = wt.to_json()
        assert json.loads(json_str) == []

    def test_indent_zero(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json(indent=0)
        assert json.loads(json_str) == [{"name": "Alice"}]

    def test_indent_none(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json(indent=None)
        assert "\n" not in json_str
        assert json.loads(json_str) == [{"name": "Alice"}]

    def test_sort_keys(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        json_str = wt.to_json(sort_keys=True)
        assert json_str.index("age") < json_str.index("name")

    def test_default_handler(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json(default=str)
        assert json.loads(json_str) == [{"name": "Alice"}]


class TestIteration:
    def test_iter(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        rows = [r for r in wt]
        assert rows == [{"name": "Alice"}, {"name": "Bob"}]

    def test_iter_returns_copies(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        for row in wt:
            row["name"] = "modified"
        assert wt.as_dicts()[0]["name"] == "Alice"

    def test_getitem(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt[0] == {"name": "Alice", "age": "30"}
        assert wt[1] == {"name": "Bob", "age": "25"}

    def test_getitem_returns_copy(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        row = wt[0]
        row["name"] = "modified"
        assert wt[0]["name"] == "Alice"

    def test_getitem_index_error(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(IndexError):
            wt[5]

    def test_getitem_slice(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        result = wt[0:2]
        assert len(result) == 2
        assert result[0] == {"name": "Alice"}
        assert result[1] == {"name": "Bob"}

    def test_getitem_slice_returns_copies(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        rows = wt[0:2]
        rows[0]["name"] = "modified"
        assert wt[0]["name"] == "Alice"

    def test_getitem_slice_empty(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt[5:10] == []

    def test_len(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        assert len(wt) == 3

    def test_len_empty(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert len(wt) == 0


class TestHeaders:
    def test_basic(self, make_table):
        table = make_table(["name", "age", "email"], [])
        wt = wrap(table)
        assert wt.headers == ["name", "age", "email"]

    def test_returns_copy(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        headers = wt.headers
        headers.append("extra")
        assert wt.headers == ["name"]


class TestExtractRows:
    def test_row_with_getitem_no_as_dict(self, make_table):
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

    def test_unsupported_row_type(self, make_table):
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
    def test_repr(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        r = repr(wt)
        assert "TableWrapper" in r
        assert "name" in r
        assert "rows=2" in r


class TestEq:
    def test_equal(self, make_table):
        t1 = make_table(["name"], [["Alice"], ["Bob"]])
        t2 = make_table(["name"], [["Alice"], ["Bob"]])
        assert wrap(t1) == wrap(t2)

    def test_not_equal_rows(self, make_table):
        t1 = make_table(["name"], [["Alice"]])
        t2 = make_table(["name"], [["Bob"]])
        assert wrap(t1) != wrap(t2)

    def test_not_equal_headers(self, make_table):
        t1 = make_table(["name"], [["Alice"]])
        t2 = make_table(["age"], [["Alice"]])
        assert wrap(t1) != wrap(t2)

    def test_not_equal_to_non_wrapper(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt != "not a wrapper"
        assert wt != 42


class TestContains:
    def test_present(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        assert {"name": "Alice"} in wt

    def test_absent(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert {"name": "Charlie"} not in wt

    def test_partial_match_absent(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        assert {"name": "Alice"} not in wt


class TestEdgeCases:
    """Edge cases for TableWrapper."""

    def test_getitem_negative_index(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        assert wt[-1] == {"name": "Charlie"}
        assert wt[-2] == {"name": "Bob"}

    def test_getitem_negative_index_out_of_range(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(IndexError):
            wt[-5]

    def test_getitem_slice_negative(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"], ["Charlie"]])
        wt = wrap(table)
        result = wt[-2:]
        assert len(result) == 2
        assert result[0] == {"name": "Bob"}
        assert result[1] == {"name": "Charlie"}

    def test_getitem_slice_step(self, make_table):
        table = make_table(["name"], [["A"], ["B"], ["C"], ["D"]])
        wt = wrap(table)
        result = wt[::2]
        assert len(result) == 2
        assert result[0] == {"name": "A"}
        assert result[1] == {"name": "C"}

    def test_getitem_slice_full(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        result = wt[:]
        assert len(result) == 2

    def test_getitem_slice_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt[:] == []

    def test_find_row_nonexistent_column(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.find_row(nonexistent="value") is None

    def test_find_all_rows_nonexistent_column(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt.find_all_rows(nonexistent="value") == []

    def test_find_row_multiple_matches_returns_first(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "30"]])
        wt = wrap(table)
        result = wt.find_row(age="30")
        assert result == {"name": "Alice", "age": "30"}

    def test_find_all_rows_all_match(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "30"]])
        wt = wrap(table)
        result = wt.find_all_rows(age="30")
        assert len(result) == 2

    def test_validate_columns_strict_exact_match(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        wt.validate_columns("name", "age", strict=True)

    def test_validate_columns_strict_empty_expected_with_columns(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError, match="unexpected columns"):
            wt.validate_columns(strict=True)

    def test_validate_columns_strict_empty_table_empty_expected(self, make_table):
        table = make_table([], [])
        wt = wrap(table)
        wt.validate_columns(strict=True)

    def test_validate_columns_duplicate_expected(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        wt.validate_columns("name", "name")

    def test_validate_columns_strict_duplicate_extra(self, make_table):
        table = make_table(["name", "extra"], [])
        wt = wrap(table)
        with pytest.raises(ColumnMismatchError) as exc_info:
            wt.validate_columns("name", strict=True)
        assert exc_info.value.extra == ["extra"]

    def test_column_empty_string_value(self, make_table):
        table = make_table(["name"], [[""]])
        wt = wrap(table)
        assert wt.column("name") == [""]

    def test_column_special_chars_in_header(self, make_table):
        table = make_table(["naïve", "café"], [["value1", "value2"]])
        wt = wrap(table)
        assert wt.column("café") == ["value2"]

    def test_as_dicts_does_not_leak_internal_refs(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        dicts1 = wt.as_dicts()
        dicts2 = wt.as_dicts()
        assert dicts1[0] is not dicts2[0]

    def test_transpose_single_row(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert transposed.headers == ["_column", "0"]
        assert transposed.as_dicts() == [
            {"_column": "name", "0": "Alice"},
            {"_column": "age", "0": "30"},
        ]

    def test_transpose_single_column(self, make_table):
        table = make_table(["name"], [["Alice"], ["Bob"]])
        wt = wrap(table)
        transposed = wt.transpose()
        assert transposed.headers == ["_column", "0", "1"]
        assert transposed.as_dicts() == [
            {"_column": "name", "0": "Alice", "1": "Bob"},
        ]

    def test_transpose_preserves_original(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        original = wt.as_dicts()
        wt.transpose()
        assert wt.as_dicts() == original

    def test_transpose_double_transpose_not_identity(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        double = wt.transpose().transpose()
        assert double.headers[0] == "_column"

    def test_to_csv_quoting_nonnumeric(self, make_table):
        import csv as csv_module

        table = make_table(["name"], [["Alice, Jr"]])
        wt = wrap(table)
        csv_str = wt.to_csv(quoting=csv_module.QUOTE_MINIMAL)
        assert '"Alice, Jr"' in csv_str

    def test_to_csv_tab_delimiter(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        csv_str = wt.to_csv(delimiter="\t")
        lines = csv_str.split("\n")
        assert lines[0] == "name\tage"
        assert lines[1] == "Alice\t30"

    def test_to_json_ensure_ascii_false(self, make_table):
        table = make_table(["name"], [["café"]])
        wt = wrap(table)
        json_str = wt.to_json()
        assert "café" in json_str

    def test_to_json_sort_keys_multi_keys(self, make_table):
        table = make_table(["z", "a", "m"], [["1", "2", "3"]])
        wt = wrap(table)
        json_str = wt.to_json(sort_keys=True)
        assert json_str.index('"a"') < json_str.index('"m"') < json_str.index('"z"')

    def test_to_json_indent_default(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        json_str = wt.to_json()
        assert "\n" in json_str
        assert "  " in json_str

    def test_eq_same_instance(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert wt == wt

    def test_eq_different_table_impl_same_data(self, make_table):
        from behave_tables._table_impl import SimpleTable

        t1 = make_table(["name"], [["Alice"]])
        t2 = SimpleTable(headings=["name"], rows_data=[{"name": "Alice"}])
        assert wrap(t1) == wrap(t2)

    def test_eq_empty_tables(self, make_table):
        t1 = make_table(["name"], [])
        t2 = make_table(["name"], [])
        assert wrap(t1) == wrap(t2)

    def test_eq_different_column_order_not_equal(self, make_table):
        t1 = make_table(["name", "age"], [["Alice", "30"]])
        t2 = make_table(["age", "name"], [["30", "Alice"]])
        assert wrap(t1) != wrap(t2)

    def test_contains_empty_dict_in_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert {} not in wt

    def test_contains_empty_dict_in_nonempty_table(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        assert {} not in wt

    def test_contains_exact_match_multiple_columns(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        assert {"name": "Alice", "age": "30"} in wt

    def test_headers_empty_table(self, make_table):
        table = make_table([], [])
        wt = wrap(table)
        assert wt.headers == []

    def test_iter_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        assert list(wt) == []

    def test_repr_empty_table(self, make_table):
        table = make_table(["name"], [])
        wt = wrap(table)
        r = repr(wt)
        assert "rows=0" in r

    def test_repr_single_row(self, make_table):
        table = make_table(["x"], [["1"]])
        wt = wrap(table)
        r = repr(wt)
        assert "rows=1" in r

    def test_hash_is_none(self, make_table):
        table = make_table(["x"], [["1"]])
        wt = wrap(table)
        with pytest.raises(TypeError, match="unhashable"):
            hash(wt)
