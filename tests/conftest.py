"""Shared test fixtures — mock behave Table and Row objects."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import pytest


@dataclass
class FakeRow:
    """Mimics behave.model.Row."""

    cells: list[str]
    headings: list[str]

    def as_dict(self) -> dict[str, str]:
        return dict(zip(self.headings, self.cells, strict=True))

    def __getitem__(self, key: str) -> str:
        idx = self.headings.index(key)
        return self.cells[idx]


@dataclass
class FakeTable:
    """Mimics behave.model.Table."""

    headings: list[str]
    rows_cells: list[list[str]] = field(default_factory=list)

    @property
    def rows(self) -> list[FakeRow]:
        return [FakeRow(cells=c, headings=self.headings) for c in self.rows_cells]


def _make_table(
    headings: list[str],
    rows: list[list[str]],
) -> FakeTable:
    """Build a FakeTable for testing."""
    return FakeTable(headings=headings, rows_cells=rows)


@pytest.fixture
def make_table() -> Callable[[list[str], list[list[str]]], FakeTable]:
    """Return a factory that builds FakeTable instances."""
    return _make_table
