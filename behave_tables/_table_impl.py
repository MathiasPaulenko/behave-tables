"""Internal table implementation for transpose() and testing.

This module provides minimal implementations of the table and row
protocols so that ``TableWrapper`` can be constructed without a real
``behave.model.Table``. It is used internally by ``transpose()`` and
by the test suite.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SimpleRow:
    """A minimal row implementation compatible with ``TableWrapper``.

    Attributes:
        _data: The dict backing this row's column-value mappings.
    """

    _data: dict[str, str]

    def as_dict(self) -> dict[str, str]:
        """Return a copy of the row's column-value mapping.

        Returns:
            A dict mapping column names to string values.
        """
        return dict(self._data)

    def __getitem__(self, key: str) -> str:
        """Return the value for the given column name.

        Args:
            key: The column name.

        Returns:
            The string value for that column.

        Raises:
            KeyError: If the column name is not in the row.
        """
        return self._data[key]


@dataclass
class SimpleTable:
    """A minimal table implementation compatible with ``TableWrapper``.

    Attributes:
        headings: The column header names.
        rows_data: The row data as a list of dicts.
    """

    headings: list[str]
    rows_data: list[dict[str, str]] = field(default_factory=list)

    @property
    def rows(self) -> list[SimpleRow]:
        """Return all rows as ``SimpleRow`` instances.

        Returns:
            A list of ``SimpleRow`` objects, one per entry in ``rows_data``.
        """
        return [SimpleRow(d) for d in self.rows_data]
