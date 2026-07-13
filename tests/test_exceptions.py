"""Tests for exceptions."""

from __future__ import annotations

import pytest

from behave_tables import ColumnMismatchError


class TestColumnMismatchError:
    def test_missing_only(self):
        err = ColumnMismatchError(missing=["email", "phone"])
        assert "email" in str(err)
        assert "phone" in str(err)
        assert err.missing == ["email", "phone"]
        assert err.extra == []

    def test_missing_and_extra(self):
        err = ColumnMismatchError(missing=["email"], extra=["id"])
        assert "missing" in str(err)
        assert "unexpected" in str(err)
        assert err.extra == ["id"]

    def test_is_value_error(self):
        err = ColumnMismatchError(missing=["x"])
        assert isinstance(err, ValueError)
