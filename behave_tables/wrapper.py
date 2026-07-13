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
    """Protocol for behave.model.Table or any table-like object."""

    headings: list[str]

    @property
    def rows(self) -> list[Any]: ...


class RowLike(Protocol):
    """Protocol for behave.model.Row or any row-like object."""

    def as_dict(self) -> dict[str, str]: ...

    def __getitem__(self, key: str) -> str: ...


class TableWrapper:
    """Wraps a behave.model.Table with an ergonomic API.

    Zero dependencies. Works with any table-like object that has
    ``headings`` (list[str]) and ``rows`` (list of objects with
    ``as_dict()`` or ``__getitem__``).
    """

    def __init__(self, table: TableLike) -> None:
        self._table = table
        self._rows: list[dict[str, str]] = self._extract_rows(table)

    @staticmethod
    def _extract_rows(table: TableLike) -> list[dict[str, str]]:
        """Extract rows as list of dicts from any table-like object."""
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
        """Return column headers."""
        return list(self._table.headings)

    def as_dicts(self) -> list[dict[str, str]]:
        """Return all rows as a list of dicts (copies)."""
        return [dict(row) for row in self._rows]

    def as_models(self, model: type) -> list[Any]:
        """Convert all rows to model instances.

        Supports Pydantic v2 BaseModel and stdlib dataclasses.
        """
        return [convert_row_to_model(row, model) for row in self._rows]

    def column(self, name: str) -> list[str]:
        """Return all values for a single column.

        Raises KeyError if the column does not exist.
        """
        if name not in self.headers:
            raise KeyError(
                f"Column {name!r} not found. Available: {self.headers}"
            )
        return [row[name] for row in self._rows]

    def find_row(self, **filters: str) -> dict[str, str] | None:
        """Return the first row matching all filters, or None."""
        if not filters:
            return self._rows[0] if self._rows else None
        for row in self._rows:
            if all(row.get(k) == v for k, v in filters.items()):
                return row
        return None

    def validate_columns(self, *expected: str) -> None:
        """Raise ColumnMismatchError if expected columns are missing."""
        headers = set(self.headers)
        missing = [col for col in expected if col not in headers]
        if missing:
            raise ColumnMismatchError(missing=missing)

    def transpose(self) -> TableWrapper:
        """Return a new TableWrapper with rows and columns swapped.

        Original headers become the first column.
        Original row indices become the new headers.
        """
        from behave_tables._mock import MockTable

        new_headers = [str(i) for i in range(len(self._rows))]
        new_rows: list[dict[str, str]] = []

        for header in self.headers:
            row_dict: dict[str, str] = {"_column": header}
            for row_idx, row in enumerate(self._rows):
                row_dict[str(row_idx)] = row[header]
            new_rows.append(row_dict)

        mock = MockTable(
            headings=["_column"] + new_headers,
            rows_data=new_rows,
        )
        return TableWrapper(mock)

    def to_csv(self) -> str:
        """Return table as a CSV string."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.headers)
        writer.writeheader()
        writer.writerows(self._rows)
        return output.getvalue().replace("\r\n", "\n").rstrip("\n")

    def to_json(self, indent: int = 2) -> str:
        """Return table as a JSON string (list of objects)."""
        return json.dumps(self._rows, indent=indent, ensure_ascii=False)

    def __iter__(self) -> Iterator[dict[str, str]]:
        return iter(self._rows)

    def __getitem__(self, index: int) -> dict[str, str]:
        return self._rows[index]

    def __len__(self) -> int:
        return len(self._rows)

    def __repr__(self) -> str:
        return f"TableWrapper(headers={self.headers!r}, rows={len(self)})"
