"""behave-tables — Polished API for Behave Data Tables.

A thin wrapper around ``behave.model.Table`` that provides ergonomic
methods for converting data tables to dicts, Pydantic models,
dataclasses, CSV, JSON, and JSON Lines. Supports column selection,
renaming, sorting, deduplication, and round-trip import/export.

Example:
    >>> from behave_tables import wrap
    >>> table = wrap(context.table)
    >>> rows = table.as_dicts()
"""

from __future__ import annotations

from .exceptions import ColumnMismatchError
from .wrapper import TableLike, TableWrapper

__version__ = "1.3.0"

__all__ = ["TableWrapper", "wrap", "ColumnMismatchError", "TableLike", "__version__"]


def wrap(table: TableLike) -> TableWrapper:
    """Wrap a behave.model.Table with ``TableWrapper``.

    Convenience function: ``wrap(context.table)`` instead of
    ``TableWrapper(context.table)``.

    Args:
        table: A table-like object with ``headings`` and ``rows``.

    Returns:
        A ``TableWrapper`` instance ready to use.
    """
    return TableWrapper(table)
