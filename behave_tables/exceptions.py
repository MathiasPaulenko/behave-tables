"""Custom exceptions for behave-tables."""

from __future__ import annotations


class ColumnMismatchError(ValueError):
    """Raised when expected columns are not found in the table."""

    def __init__(self, missing: list[str], extra: list[str] | None = None) -> None:
        parts = [f"missing columns: {missing}"] if missing else []
        if extra:
            parts.append(f"unexpected columns: {extra}")
        super().__init__("; ".join(parts))
        self.missing = missing
        self.extra = extra or []
