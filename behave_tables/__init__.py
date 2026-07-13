"""behave-tables — Polished API for Behave Data Tables."""

from __future__ import annotations

from .exceptions import ColumnMismatchError
from .wrapper import TableWrapper

__version__ = "1.0.0"

__all__ = ["TableWrapper", "wrap", "ColumnMismatchError", "__version__"]


def wrap(table: object) -> TableWrapper:
    """Wrap a behave.model.Table with TableWrapper.

    Convenience function: ``wrap(context.table)`` instead of
    ``TableWrapper(context.table)``.
    """
    return TableWrapper(table)
