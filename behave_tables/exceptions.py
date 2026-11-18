"""Custom exceptions for behave-tables."""

from __future__ import annotations


class ColumnMismatchError(ValueError):
    """Raised when expected columns are not found in the table.

    Attributes:
        missing: List of column names that were expected but not found.
        extra: List of unexpected column names (if any were detected).
    """

    def __init__(self, missing: list[str], extra: list[str] | None = None) -> None:
        """Initialize the error with missing and optional extra columns.

        Args:
            missing: Column names that were expected but not present.
            extra: Column names that were present but not expected.
        """
        self.missing = list(missing)
        self.extra = list(extra or [])
        parts = [f"missing columns: {self.missing}"] if self.missing else []
        if self.extra:
            parts.append(f"unexpected columns: {self.extra}")
        super().__init__("; ".join(parts) or "no column mismatch")

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the error."""
        return f"ColumnMismatchError(missing={self.missing!r}, extra={self.extra!r})"

    def __reduce__(self) -> tuple[type, tuple[list[str], list[str]]]:
        """Support pickling so ``missing``/``extra`` and the message survive."""
        return (type(self), (self.missing, self.extra))
