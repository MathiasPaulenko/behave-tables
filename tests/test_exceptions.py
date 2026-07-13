"""Tests for exceptions."""

from __future__ import annotations

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

    def test_empty_missing_and_extra(self):
        err = ColumnMismatchError(missing=[])
        assert "no column mismatch" in str(err)
        assert err.missing == []
        assert err.extra == []

    def test_repr(self):
        err = ColumnMismatchError(missing=["name"], extra=["extra"])
        r = repr(err)
        assert "ColumnMismatchError" in r
        assert "missing" in r
        assert "extra" in r
