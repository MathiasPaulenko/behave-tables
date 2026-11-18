"""Tests for TableWrapper core methods."""

from __future__ import annotations

import json

import pytest

from behave_tables import ColumnMismatchError, TableWrapper, wrap


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

    def test_missing_value_in_row(self):
        from behave_tables._table_impl import SimpleTable

        mock = SimpleTable(headings=["a", "b"], rows_data=[{"a": "1"}])
        wt = wrap(mock)
        assert wt.column("b") == [""]


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

    def test_crlf_in_value_preserved(self):
        from behave_tables import TableWrapper
        from behave_tables._table_impl import SimpleTable

        mock = SimpleTable(headings=["name"], rows_data=[{"name": "a\r\nb"}])
        wt = wrap(mock)
        csv_str = wt.to_csv()
        assert '"a\r\nb"' in csv_str
        restored = TableWrapper.from_csv(csv_str)
        assert restored.as_dicts() == [{"name": "a\r\nb"}]

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


class TestRealBehaveTable:
    """Integration tests against a real behave.model.Table."""

    def test_wrap_real_table(self):
        pytest.importorskip("behave")
        from behave.model import Table

        table = Table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.as_dicts() == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"},
        ]
        assert wt.headers == ["name", "age"]
        assert wt.column("name") == ["Alice", "Bob"]

    def test_operations_on_real_table(self):
        pytest.importorskip("behave")
        from behave.model import Table

        table = Table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        assert wt.find_row(name="Bob") == {"name": "Bob", "age": "25"}
        assert wt.select("name").headers == ["name"]
        assert wt.sort("age").as_dicts()[0]["name"] == "Bob"
        assert wt.count() == 2


class TestConstructionValidation:
    def test_none_raises_type_error(self):
        with pytest.raises(TypeError, match="headings.*rows"):
            wrap(None)

    def test_non_table_objects_raise(self):
        for bad in (42, object(), {"headings": ["a"]}, "string"):
            with pytest.raises(TypeError, match="headings.*rows"):
                wrap(bad)

    def test_missing_rows_attr_raises(self):
        class NoRows:
            headings = ["a"]

        with pytest.raises(TypeError, match="headings.*rows"):
            wrap(NoRows())

    def test_missing_headings_attr_raises(self):
        class NoHeadings:
            rows = []

        with pytest.raises(TypeError, match="headings.*rows"):
            wrap(NoHeadings())

    def test_string_headings_raises(self):
        class StringHeadings:
            headings = "name"
            rows = []

        with pytest.raises(TypeError, match="iterable of column names"):
            wrap(StringHeadings())

    def test_bytes_headings_raises(self):
        class BytesHeadings:
            headings = b"name"
            rows = []

        with pytest.raises(TypeError, match="iterable of column names"):
            wrap(BytesHeadings())

    def test_non_iterable_headings_raises(self):
        class IntHeadings:
            headings = 5
            rows = []

        with pytest.raises(TypeError, match="iterable of column names"):
            wrap(IntHeadings())

    def test_headings_generator_accepted(self):
        class GenHeadings:
            @property
            def headings(self):
                return iter(["a", "b"])

            rows = []

        wt = wrap(GenHeadings())
        assert wt.headers == ["a", "b"]


class TestTableLikeConformance:
    def test_wrap_wrapper_round_trip(self, make_table):
        wt = wrap(make_table(["name", "age"], [["Alice", "30"]]))
        wrapped = wrap(wt)
        assert wrapped == wt
        assert wrapped.as_dicts() == wt.as_dicts()

    def test_wrap_wrapper_heterogeneous_rows(self):
        wt = TableWrapper.from_json('[{"a": "1"}, {"b": "2"}]')
        assert wrap(wt) == wt

    def test_headings_property(self, make_table):
        wt = wrap(make_table(["a", "b"], []))
        assert wt.headings == ["a", "b"]
        assert wt.headings == wt.headers

    def test_headings_returns_copy(self, make_table):
        wt = wrap(make_table(["a"], []))
        wt.headings.append("x")
        assert wt.headings == ["a"]

    def test_rows_property(self, make_table):
        wt = wrap(make_table(["a", "b"], [["1", "2"]]))
        rows = wt.rows
        assert len(rows) == 1
        assert rows[0].as_dict() == {"a": "1", "b": "2"}
        assert rows[0]["a"] == "1"

    def test_rows_property_returns_copies(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        wt.rows[0].as_dict()["a"] = "modified"
        assert wt[0]["a"] == "1"


class TestHeadingsSnapshot:
    def test_appended_heading_does_not_desync(self):
        from behave_tables._table_impl import SimpleTable

        st = SimpleTable(headings=["a", "b"], rows_data=[{"a": "1", "b": "2"}])
        wt = wrap(st)
        st.headings.append("c")
        assert wt.headers == ["a", "b"]
        with pytest.raises(KeyError):
            wt.column("c")

    def test_replaced_heading_does_not_desync(self):
        from behave_tables._table_impl import SimpleTable

        st = SimpleTable(headings=["a"], rows_data=[{"a": "1"}])
        wt = wrap(st)
        st.headings[0] = "renamed"
        assert wt.headers == ["a"]
        assert wt.column("a") == ["1"]


class TestRowTypeHandling:
    def test_list_rows(self):
        class PositionalTable:
            headings = ["a", "b"]
            rows = [["1", "2"]]

        assert wrap(PositionalTable()).as_dicts() == [{"a": "1", "b": "2"}]

    def test_tuple_rows(self):
        class TupleTable:
            headings = ["a", "b"]
            rows = [("1", "2")]

        assert wrap(TupleTable()).as_dicts() == [{"a": "1", "b": "2"}]

    def test_positional_row_extra_cells_ignored(self):
        class WideRows:
            headings = ["a"]
            rows = [["1", "extra", "more"]]

        assert wrap(WideRows()).as_dicts() == [{"a": "1"}]

    def test_positional_row_too_short_filled(self):
        class ShortRows:
            headings = ["a", "b", "c"]
            rows = [["1"]]

        assert wrap(ShortRows()).as_dicts() == [{"a": "1", "b": "", "c": ""}]

    def test_as_dict_row_missing_key_filled(self):
        class Row:
            def as_dict(self):
                return {"a": "1"}

        class NarrowTable:
            headings = ["a", "b"]
            rows = [Row()]

        assert wrap(NarrowTable()).as_dicts() == [{"a": "1", "b": ""}]

    def test_as_dict_row_extra_key_dropped(self):
        class Row:
            def as_dict(self):
                return {"a": "1", "rogue": "x"}

        class ExtraTable:
            headings = ["a", "b"]
            rows = [Row()]

        assert wrap(ExtraTable()).as_dicts() == [{"a": "1", "b": ""}]

    def test_getitem_row_missing_key_filled(self):
        class Row:
            def __getitem__(self, key):
                return {"a": "1"}[key]

        class SparseGetitem:
            headings = ["a", "b"]
            rows = [Row()]

        assert wrap(SparseGetitem()).as_dicts() == [{"a": "1", "b": ""}]

    def test_getitem_row_index_or_value_error_filled(self):
        class Row:
            def __init__(self, exc):
                self._exc = exc

            def __getitem__(self, key):
                if key == "b":
                    raise self._exc
                return "1"

        for exc in (IndexError("no"), ValueError("no")):

            class Sparse:
                headings = ["a", "b"]
                rows = [Row(exc)]

            assert wrap(Sparse()).as_dicts() == [{"a": "1", "b": ""}]

    def test_non_string_values_coerced_to_json(self):
        class WideTable:
            headings = ["i", "n", "b", "d", "l"]
            rows = [{"i": 30, "n": None, "b": True, "d": {"x": 1}, "l": [1, 2]}]

        assert wrap(WideTable()).as_dicts() == [
            {"i": "30", "n": "null", "b": "true", "d": '{"x": 1}', "l": "[1, 2]"}
        ]

    def test_positional_row_non_string_values_coerced(self):
        class PosTable:
            headings = ["i", "b"]
            rows = [[7, False]]

        assert wrap(PosTable()).as_dicts() == [{"i": "7", "b": "false"}]

    def test_as_dict_row_non_string_values_coerced(self):
        class Row:
            def as_dict(self):
                return {"a": 1.5}

        class FloatTable:
            headings = ["a"]
            rows = [Row()]

        assert wrap(FloatTable()).as_dicts() == [{"a": "1.5"}]

    def test_dict_row(self):
        class DictTable:
            headings = ["a", "b"]
            rows = [{"a": "1", "b": "2"}]

        assert wrap(DictTable()).as_dicts() == [{"a": "1", "b": "2"}]

    def test_dict_row_missing_key_filled(self):
        class SparseDicts:
            headings = ["a", "b"]
            rows = [{"a": "1"}]

        assert wrap(SparseDicts()).as_dicts() == [{"a": "1", "b": ""}]

    def test_str_row_raises(self):
        class StrRows:
            headings = ["a"]
            rows = ["xy"]

        with pytest.raises(TypeError, match="Unsupported row type"):
            wrap(StrRows())

    def test_bytes_row_raises(self):
        class BytesRows:
            headings = ["a"]
            rows = [b"xy"]

        with pytest.raises(TypeError, match="Unsupported row type"):
            wrap(BytesRows())

    def test_bytearray_row_raises(self):
        class BytearrayRows:
            headings = ["a"]
            rows = [bytearray(b"xy")]

        with pytest.raises(TypeError, match="Unsupported row type"):
            wrap(BytearrayRows())

    def test_row_with_non_callable_as_dict_falls_through(self):
        class Row:
            as_dict = "not callable"

            def __getitem__(self, key):
                return {"a": "1"}[key]

        class WeirdTable:
            headings = ["a"]
            rows = [Row()]

        assert wrap(WeirdTable()).as_dicts() == [{"a": "1"}]


class TestFilterAbsentKeys:
    def test_find_row_absent_key_never_matches(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        assert wt.find_row(bogus=None) is None

    def test_find_row_none_value_no_match(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        assert wt.find_row(a=None) is None

    def test_find_all_rows_absent_key(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        assert wt.find_all_rows(bogus=None) == []

    def test_count_absent_key(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        assert wt.count(bogus=None) == 0

    def test_permissive_eq_object_does_not_match_absent_key(self, make_table):
        from unittest.mock import ANY

        wt = wrap(make_table(["a"], [["1"]]))
        assert wt.find_row(bogus=ANY) is None
        assert wt.find_all_rows(bogus=ANY) == []
        assert wt.count(bogus=ANY) == 0
        assert ANY not in wt
        # but a wildcard still matches an existing column
        assert wt.find_row(a=ANY) == {"a": "1"}
        assert {"a": ANY} in wt

    def test_find_row_heterogeneous_missing_key(self):
        wt = TableWrapper.from_json('[{"a": "1"}, {"a": "2", "b": "3"}]')
        assert wt.find_row(b="3") == {"a": "2", "b": "3"}
        assert wt.find_row(b="9") is None


class TestSubclassPropagation:
    def test_transform_methods_return_subclass(self):
        from behave_tables._table_impl import SimpleTable

        class Sub(TableWrapper):
            pass

        s = Sub(SimpleTable(headings=["a", "b"], rows_data=[{"a": "1", "b": "2"}]))
        for transformed in (
            s.select("a"),
            s.drop("b"),
            s.rename_columns({"a": "z"}),
            s.sort("a"),
            s.distinct(),
            s.transpose(),
        ):
            assert type(transformed) is Sub

    def test_from_methods_return_subclass(self):
        class Sub(TableWrapper):
            pass

        assert type(Sub.from_csv("a\n1")) is Sub
        assert type(Sub.from_json('[{"a": "1"}]')) is Sub


class TestSortKeyValidation:
    def test_non_str_non_callable_raises(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        for bad in (123, None, ["a"], {"x": 1}):
            with pytest.raises(TypeError, match="column name or a callable"):
                wt.sort(bad)

    def test_missing_str_column_still_key_error(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        with pytest.raises(KeyError, match="not found"):
            wt.sort("missing")

    def test_callable_key_cannot_mutate_internal_rows(self, make_table):
        wt = wrap(make_table(["a"], [["1"], ["2"]]))

        def mutating_key(row):
            row["a"] = "corrupted"
            return row["a"]

        wt.sort(key=mutating_key)
        assert wt.as_dicts() == [{"a": "1"}, {"a": "2"}]


class TestRenameMappingValidation:
    def test_non_mapping_raises(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        for bad in (["a"], "a", 5, None):
            with pytest.raises(TypeError, match="mapping"):
                wt.rename_columns(bad)

    def test_custom_mapping_accepted(self, make_table):
        from collections import UserDict

        wt = wrap(make_table(["a"], [["1"]]))
        result = wt.rename_columns(UserDict({"a": "z"}))
        assert result.headers == ["z"]

    def test_non_string_new_name_raises(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        for bad_new in (None, 5, ["x"], b"x"):
            with pytest.raises(TypeError, match="must be strings"):
                wt.rename_columns({"a": bad_new})

    def test_non_str_new_name_takes_priority_over_missing_old(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        with pytest.raises(KeyError, match="not found"):
            wt.rename_columns({"missing": "x"})


class TestFromCsvValidation:
    def test_non_string_raises(self):
        for bad in (None, b"a,b\n1,2", 123, ["a"]):
            with pytest.raises(TypeError, match="csv_string"):
                TableWrapper.from_csv(bad)

    def test_bom_stripped(self):
        wt = TableWrapper.from_csv("\ufeffa,b\n1,2")
        assert wt.headers == ["a", "b"]
        assert wt.as_dicts() == [{"a": "1", "b": "2"}]

    def test_leading_blank_lines_ignored(self):
        for prefix in ("\n", "\r\n", "\n\n", "\r\n\r\n"):
            wt = TableWrapper.from_csv(prefix + "a,b\n1,2")
            assert wt.headers == ["a", "b"]
            assert wt.as_dicts() == [{"a": "1", "b": "2"}]


class TestFromJsonValidation:
    def test_non_string_raises(self):
        for bad in (None, b'[{"a": "1"}]', 123, [{"a": "1"}]):
            with pytest.raises(TypeError, match="json_string"):
                TableWrapper.from_json(bad)


class TestValidateColumnsDedup:
    def test_duplicate_missing_deduped(self, make_table):
        wt = wrap(make_table(["a"], []))
        with pytest.raises(ColumnMismatchError) as exc_info:
            wt.validate_columns("q", "q", "r")
        assert exc_info.value.missing == ["q", "r"]

    def test_duplicate_extra_deduped(self):
        from behave_tables._table_impl import SimpleTable

        st = SimpleTable(headings=["a", "a"], rows_data=[{"a": "1"}])
        wt = wrap(st)
        with pytest.raises(ColumnMismatchError) as exc_info:
            wt.validate_columns(strict=True)
        assert exc_info.value.extra == ["a"]


class TestContainsNonDict:
    def test_non_dict_items_not_contained(self, make_table):
        wt = wrap(make_table(["a"], [["1"]]))
        for item in ("x", 42, None, ["a"], ("a",)):
            assert item not in wt
