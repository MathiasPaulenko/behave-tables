"""Internal mock table for transpose() and testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MockRow:
    """A minimal row implementation compatible with TableWrapper."""

    _data: dict[str, str]

    def as_dict(self) -> dict[str, str]:
        return dict(self._data)

    def __getitem__(self, key: str) -> str:
        return self._data[key]


@dataclass
class MockTable:
    """A minimal table implementation compatible with TableWrapper."""

    headings: list[str]
    rows_data: list[dict[str, str]] = field(default_factory=list)

    @property
    def rows(self) -> list[MockRow]:
        return [MockRow(d) for d in self.rows_data]
