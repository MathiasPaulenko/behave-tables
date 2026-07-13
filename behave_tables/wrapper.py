"""TableWrapper — polished API for Behave Data Tables."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from typing import Any, Protocol, overload

from .converters import convert_row_to_model
from .exceptions import ColumnMismatchError


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

    def as_models(self, model: type) -> list[Any]:
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
                f"Column {name!r} not found. Available: {self.headers}"
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
        from ._mock import MockTable

        new_headers = [str(i) for i in range(len(self._rows))]
        new_rows: list[dict[str, str]] = []

        for header in self.headers:
            row_dict: dict[str, str] = {"_column": header}
            for row_idx, row in enumerate(self._rows):
                row_dict[str(row_idx)] = row.get(header, "")
            new_rows.append(row_dict)

        mock = MockTable(
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

    def __len__(self) -> int:
        """Return the number of rows."""
        return len(self._rows)

    def __repr__(self) -> str:
        return f"TableWrapper(headers={self.headers!r}, rows={len(self)})"
