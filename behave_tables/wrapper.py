"""TableWrapper — polished API for Behave Data Tables."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Callable, Iterator
from typing import Any, Protocol, TypeVar, overload

from ._table_impl import SimpleTable
from .converters import convert_row_to_model
from .exceptions import ColumnMismatchError

M = TypeVar("M")


class TableLike(Protocol):
    """Protocol for behave.model.Table or any table-like object.

    Any object with ``headings`` (list[str]) and a ``rows`` property
    yielding row-like objects can be wrapped.
    """

    headings: list[str]

    @property
    def rows(self) -> list[Any]: ...


class TableWrapper:
    """Wraps a behave.model.Table with an ergonomic API.

    Zero dependencies. Works with any table-like object that has
    ``headings`` (list[str]) and ``rows`` (list of objects with
    ``as_dict()`` or ``__getitem__``).

    All public methods return copies of internal data to prevent
    accidental mutation of wrapper state.

    Example:
        >>> table = wrap(context.table)
        >>> users = table.as_dicts()
        >>> alice = table.find_row(name="Alice")
    """

    def __init__(self, table: TableLike) -> None:
        """Initialize the wrapper and extract rows from the table.

        Args:
            table: A table-like object with ``headings`` and ``rows``.
        """
        self._table = table
        self._rows: list[dict[str, str]] = self._extract_rows(table)

    @staticmethod
    def _extract_rows(table: TableLike) -> list[dict[str, str]]:
        """Extract rows as list of dicts from any table-like object.

        Handles rows that expose ``as_dict()`` (behave.model.Row) or
        support ``__getitem__`` with header names as keys.

        Args:
            table: A table-like object with ``headings`` and ``rows``.

        Returns:
            A list of dicts mapping column names to string values.

        Raises:
            TypeError: If a row has neither ``as_dict`` nor ``__getitem__``.
        """
        rows: list[dict[str, str]] = []
        for row in table.rows:
            if hasattr(row, "as_dict"):
                rows.append(dict(row.as_dict()))
            elif hasattr(row, "__getitem__"):
                rows.append({h: row[h] for h in table.headings})
            else:
                raise TypeError(f"Unsupported row type: {type(row)!r}")
        return rows

    @property
    def headers(self) -> list[str]:
        """Return a copy of the column headers.

        Returns:
            A list of column name strings.
        """
        return list(self._table.headings)

    def as_dicts(self) -> list[dict[str, str]]:
        """Return all rows as a list of dicts (copies).

        Returns:
            A list of dicts, each mapping column names to string values.
            Modifying the returned dicts does not affect the wrapper.
        """
        return [dict(row) for row in self._rows]

    def as_models(self, model: type[M]) -> list[M]:
        """Convert all rows to model instances.

        Detects Pydantic v2 ``BaseModel`` and stdlib ``dataclass``
        automatically. Pydantic performs validation and type coercion;
        dataclasses receive string values as-is.

        Only columns that match the model's fields are passed; extra
        columns in the table are silently ignored.

        Args:
            model: A Pydantic ``BaseModel`` subclass or a ``dataclass``.

        Returns:
            A list of model instances, one per row.

        Raises:
            TypeError: If ``model`` is not a Pydantic model or dataclass.
            ValidationError: If Pydantic validation fails for any row.
        """
        return [convert_row_to_model(row, model) for row in self._rows]

    def column(self, name: str) -> list[str]:
        """Return all values for a single column.

        Args:
            name: The column header name.

        Returns:
            A list of string values, one per row, in row order.

        Raises:
            KeyError: If the column does not exist in the table.
        """
        if name not in self._table.headings:
            raise KeyError(
                f"Column {name!r} not found. Available: {self._table.headings}"
            )
        return [row[name] for row in self._rows]

    def find_row(self, **filters: str) -> dict[str, str] | None:
        """Return the first row matching all filters, or ``None``.

        If no filters are provided, returns the first row (or ``None``
        if the table is empty).

        Args:
            **filters: Column-value pairs that must all match.

        Returns:
            A copy of the matching row dict, or ``None`` if no match.
        """
        if not filters:
            return dict(self._rows[0]) if self._rows else None
        for row in self._rows:
            if all(row.get(k) == v for k, v in filters.items()):
                return dict(row)
        return None

    def find_all_rows(self, **filters: str) -> list[dict[str, str]]:
        """Return all rows matching all filters (copies).

        If no filters are provided, returns all rows.

        Args:
            **filters: Column-value pairs that must all match.

        Returns:
            A list of copies of matching row dicts.
        """
        if not filters:
            return self.as_dicts()
        return [
            dict(row)
            for row in self._rows
            if all(row.get(k) == v for k, v in filters.items())
        ]

    def validate_columns(self, *expected: str, strict: bool = False) -> None:
        """Validate that expected columns exist in the table.

        Args:
            *expected: Column names that must be present.
            strict: If ``True``, also raise when the table has columns
                not listed in *expected.

        Raises:
            ColumnMismatchError: If any expected column is missing, or
                (with ``strict=True``) if any unexpected column is present.
        """
        headers = set(self._table.headings)
        expected_set = set(expected)
        missing = [col for col in expected if col not in headers]
        extra = [col for col in self._table.headings if col not in expected_set] if strict else []
        if missing or extra:
            raise ColumnMismatchError(missing=missing, extra=extra)

    def transpose(self) -> TableWrapper:
        """Return a new ``TableWrapper`` with rows and columns swapped.

        Original headers become the first column (``"_column"``) and
        original row indices become the new headers (``"0"``, ``"1"``, ...).

        Returns:
            A new ``TableWrapper`` instance with the transposed data.
        """
        new_headers = [str(i) for i in range(len(self._rows))]
        new_rows: list[dict[str, str]] = []

        for header in self.headers:
            row_dict: dict[str, str] = {"_column": header}
            for row_idx, row in enumerate(self._rows):
                row_dict[str(row_idx)] = row.get(header, "")
            new_rows.append(row_dict)

        mock = SimpleTable(
            headings=["_column"] + new_headers,
            rows_data=new_rows,
        )
        return TableWrapper(mock)

    def to_csv(
        self,
        delimiter: str = ",",
        quoting: int = csv.QUOTE_MINIMAL,
    ) -> str:
        """Return the table as a CSV string.

        Uses the table headers as the CSV header row. Missing values
        are written as empty strings; extra keys in rows are ignored.

        Args:
            delimiter: Column separator character (default ``,``).
            quoting: CSV quoting level (default ``QUOTE_MINIMAL``).
                See :mod:`csv` for valid values.

        Returns:
            A CSV-formatted string with headers and all rows.
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.headers,
            restval="",
            extrasaction="ignore",
            delimiter=delimiter,
            quoting=quoting,
        )
        writer.writeheader()
        writer.writerows(self._rows)
        return output.getvalue().replace("\r\n", "\n").rstrip("\n")

    def to_json(
        self,
        indent: int | None = 2,
        sort_keys: bool = False,
        default: Any = None,
    ) -> str:
        """Return the table as a JSON string (list of objects).

        Args:
            indent: Number of spaces for indentation. Use ``0`` for
                compact output with newlines, or ``None`` for a single
                line.
            sort_keys: If ``True``, sort object keys alphabetically.
            default: A function called for objects that cannot be
                serialized by default. See :func:`json.dumps`.

        Returns:
            A JSON-formatted string representing a list of row objects.
        """
        return json.dumps(
            self.as_dicts(),
            indent=indent,
            ensure_ascii=False,
            sort_keys=sort_keys,
            default=default,
        )

    def select(self, *columns: str) -> TableWrapper:
        """Return a new wrapper with only the specified columns.

        Args:
            *columns: Column names to keep. Order determines the new
                column order.

        Returns:
            A new ``TableWrapper`` with only the selected columns.

        Raises:
            KeyError: If any column does not exist in the table.
        """
        headings = self._table.headings
        for col in columns:
            if col not in headings:
                raise KeyError(
                    f"Column {col!r} not found. Available: {headings}"
                )
        new_rows = [{col: row.get(col, "") for col in columns} for row in self._rows]
        return TableWrapper(SimpleTable(headings=list(columns), rows_data=new_rows))

    def drop(self, *columns: str) -> TableWrapper:
        """Return a new wrapper without the specified columns.

        Args:
            *columns: Column names to exclude.

        Returns:
            A new ``TableWrapper`` with the remaining columns.

        Raises:
            KeyError: If any column does not exist in the table.
        """
        headings = self._table.headings
        for col in columns:
            if col not in headings:
                raise KeyError(
                    f"Column {col!r} not found. Available: {headings}"
                )
        keep = [h for h in headings if h not in columns]
        new_rows = [{col: row.get(col, "") for col in keep} for row in self._rows]
        return TableWrapper(SimpleTable(headings=keep, rows_data=new_rows))

    def rename_columns(self, mapping: dict[str, str]) -> TableWrapper:
        """Return a new wrapper with renamed columns.

        Args:
            mapping: A dict mapping old column names to new names.

        Returns:
            A new ``TableWrapper`` with renamed columns.

        Raises:
            KeyError: If any old column name does not exist.
        """
        headings = self._table.headings
        for old in mapping:
            if old not in headings:
                raise KeyError(
                    f"Column {old!r} not found. Available: {headings}"
                )
        new_headings = [mapping.get(h, h) for h in headings]
        new_rows = [
            {mapping.get(k, k): v for k, v in row.items()} for row in self._rows
        ]
        return TableWrapper(SimpleTable(headings=new_headings, rows_data=new_rows))

    def sort(
        self,
        key: str | Callable[[dict[str, str]], Any],
        reverse: bool = False,
    ) -> TableWrapper:
        """Return a new wrapper with rows sorted by the given key.

        Args:
            key: A column name to sort by, or a callable that receives
                a row dict and returns a sort key.
            reverse: If ``True``, sort in descending order.

        Returns:
            A new ``TableWrapper`` with sorted rows.
        """
        if callable(key):
            key_func: Callable[[dict[str, str]], Any] = key
        else:
            if key not in self._table.headings:
                raise KeyError(
                    f"Column {key!r} not found. Available: {self._table.headings}"
                )
            col_name = key

            def key_func(row: dict[str, str]) -> Any:
                return row.get(col_name, "")
        new_rows = sorted(self._rows, key=key_func, reverse=reverse)
        return TableWrapper(
            SimpleTable(headings=list(self._table.headings), rows_data=new_rows)
        )

    def unique(self, column: str) -> list[str]:
        """Return unique values for a column, preserving first-seen order.

        Args:
            column: The column name.

        Returns:
            A list of unique string values in first-seen order.

        Raises:
            KeyError: If the column does not exist.
        """
        if column not in self._table.headings:
            raise KeyError(
                f"Column {column!r} not found. Available: {self._table.headings}"
            )
        seen: set[str] = set()
        result: list[str] = []
        for row in self._rows:
            val = row.get(column, "")
            if val not in seen:
                seen.add(val)
                result.append(val)
        return result

    def distinct(self) -> TableWrapper:
        """Return a new wrapper with duplicate rows removed.

        Returns:
            A new ``TableWrapper`` with only the first occurrence of
            each unique row.
        """
        seen: set[tuple[tuple[str, str], ...]] = set()
        new_rows: list[dict[str, str]] = []
        for row in self._rows:
            row_tuple = tuple(sorted(row.items()))
            if row_tuple not in seen:
                seen.add(row_tuple)
                new_rows.append(dict(row))
        return TableWrapper(
            SimpleTable(headings=list(self._table.headings), rows_data=new_rows)
        )

    def count(self, **filters: str) -> int:
        """Count rows matching all filters without materializing them.

        Args:
            **filters: Column-value pairs that must all match.

        Returns:
            The number of matching rows.
        """
        if not filters:
            return len(self._rows)
        return sum(
            1 for row in self._rows if all(row.get(k) == v for k, v in filters.items())
        )

    def first(self) -> dict[str, str] | None:
        """Return the first row as a dict copy, or ``None`` if empty.

        Returns:
            A copy of the first row dict, or ``None``.
        """
        return dict(self._rows[0]) if self._rows else None

    def last(self) -> dict[str, str] | None:
        """Return the last row as a dict copy, or ``None`` if empty.

        Returns:
            A copy of the last row dict, or ``None``.
        """
        return dict(self._rows[-1]) if self._rows else None

    def to_jsonl(self) -> str:
        """Return the table as JSON Lines (one JSON object per line).

        Returns:
            A string with one JSON object per line, no trailing newline.
        """
        return "\n".join(
            json.dumps(row, ensure_ascii=False) for row in self.as_dicts()
        )

    @classmethod
    def from_csv(cls, csv_string: str, delimiter: str = ",") -> TableWrapper:
        """Create a ``TableWrapper`` from a CSV string.

        Args:
            csv_string: A CSV-formatted string with a header row.
            delimiter: Column separator character (default ``,``).

        Returns:
            A new ``TableWrapper`` instance.
        """
        reader = csv.DictReader(io.StringIO(csv_string), delimiter=delimiter)
        headings = list(reader.fieldnames or [])
        rows_data = [dict(row) for row in reader]
        return cls(SimpleTable(headings=headings, rows_data=rows_data))

    @classmethod
    def from_json(cls, json_string: str) -> TableWrapper:
        """Create a ``TableWrapper`` from a JSON string.

        The JSON must be a list of objects (as produced by ``to_json()``).
        Column names are inferred from the union of all object keys,
        preserving first-seen order.

        Args:
            json_string: A JSON-formatted string representing a list
                of row objects.

        Returns:
            A new ``TableWrapper`` instance.
        """
        data = json.loads(json_string)
        if not isinstance(data, list):
            raise TypeError(
                f"Expected a JSON list of objects, got {type(data).__name__}"
            )
        seen: set[str] = set()
        headings: list[str] = []
        for row in data:
            if not isinstance(row, dict):
                raise TypeError(
                    f"Expected each row to be a JSON object, got {type(row).__name__}"
                )
            for key in row:
                if key not in seen:
                    seen.add(key)
                    headings.append(key)
        rows_data = [dict(row) for row in data]
        return cls(SimpleTable(headings=headings, rows_data=rows_data))

    def __iter__(self) -> Iterator[dict[str, str]]:
        """Iterate over rows as dicts (copies).

        Yields:
            A copy of each row dict.
        """
        return (dict(row) for row in self._rows)

    @overload
    def __getitem__(self, index: int) -> dict[str, str]: ...
    @overload
    def __getitem__(self, index: slice) -> list[dict[str, str]]: ...

    def __getitem__(self, index: int | slice) -> dict[str, str] | list[dict[str, str]]:
        """Return a copy of the row at the given index or a list of copies for a slice.

        Args:
            index: Zero-based row index or slice.

        Returns:
            A copy of the row dict at that index, or a list of copies
            for a slice.

        Raises:
            IndexError: If the index is out of range.
        """
        if isinstance(index, slice):
            return [dict(row) for row in self._rows[index]]
        return dict(self._rows[index])

    def __contains__(self, item: dict[str, str]) -> bool:
        """Check if a row dict is present in the table.

        Args:
            item: A dict to search for (must match all keys/values).

        Returns:
            ``True`` if an equivalent row exists, ``False`` otherwise.
        """
        return item in self._rows

    def __eq__(self, other: object) -> bool:
        """Compare two wrappers by headers and rows.

        Args:
            other: Another object to compare with.

        Returns:
            ``True`` if both are ``TableWrapper`` instances with the
            same headers and rows, ``False`` otherwise.
        """
        if not isinstance(other, TableWrapper):
            return NotImplemented
        return self.headers == other.headers and self._rows == other._rows

    __hash__ = None

    def __len__(self) -> int:
        """Return the number of rows."""
        return len(self._rows)

    def __repr__(self) -> str:
        return f"TableWrapper(headers={self.headers!r}, rows={len(self)})"
