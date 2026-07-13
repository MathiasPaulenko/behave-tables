"""TableWrapper — polished API for Behave Data Tables."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterator
from typing import Any, Protocol

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

    def validate_columns(self, *expected: str) -> None:
        """Validate that expected columns exist in the table.

        Args:
            *expected: Column names that must be present.

        Raises:
            ColumnMismatchError: If any expected column is missing.
        """
        headers = set(self.headers)
        missing = [col for col in expected if col not in headers]
        if missing:
            raise ColumnMismatchError(missing=missing)

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

    def to_csv(self) -> str:
        """Return the table as a CSV string.

        Uses the table headers as the CSV header row. Missing values
        are written as empty strings; extra keys in rows are ignored.

        Returns:
            A CSV-formatted string with headers and all rows.
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.headers,
            restval="",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(self._rows)
        return output.getvalue().replace("\r\n", "\n").rstrip("\n")

    def to_json(self, indent: int | None = 2) -> str:
        """Return the table as a JSON string (list of objects).

        Args:
            indent: Number of spaces for indentation. Use ``0`` for
                compact output with newlines, or ``None`` for a single
                line.

        Returns:
            A JSON-formatted string representing a list of row objects.
        """
        return json.dumps(self._rows, indent=indent, ensure_ascii=False)

    def __iter__(self) -> Iterator[dict[str, str]]:
        """Iterate over rows as dicts (copies).

        Yields:
            A copy of each row dict.
        """
        return (dict(row) for row in self._rows)

    def __getitem__(self, index: int) -> dict[str, str]:
        """Return a copy of the row at the given index.

        Args:
            index: Zero-based row index.

        Returns:
            A copy of the row dict at that index.

        Raises:
            IndexError: If the index is out of range.
        """
        return dict(self._rows[index])

    def __len__(self) -> int:
        """Return the number of rows."""
        return len(self._rows)

    def __repr__(self) -> str:
        return f"TableWrapper(headers={self.headers!r}, rows={len(self)})"
