"""Tests for exceptions."""

from __future__ import annotations

import pickle

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

    def test_repr_missing_only(self):
        err = ColumnMismatchError(missing=["name"])
        r = repr(err)
        assert "ColumnMismatchError" in r
        assert "missing" in r
        assert "extra" in r

    def test_repr_empty(self):
        err = ColumnMismatchError(missing=[])
        r = repr(err)
        assert "ColumnMismatchError" in r

    def test_extra_defaults_to_empty_list(self):
        err = ColumnMismatchError(missing=["x"])
        assert err.extra == []

    def test_str_missing_only(self):
        err = ColumnMismatchError(missing=["a", "b"])
        s = str(err)
        assert "missing" in s
        assert "a" in s
        assert "b" in s
        assert "unexpected" not in s

    def test_str_extra_only(self):
        err = ColumnMismatchError(missing=[], extra=["x"])
        s = str(err)
        assert "unexpected" in s
        assert "x" in s
        assert "missing" not in s

    def test_str_both_missing_and_extra(self):
        err = ColumnMismatchError(missing=["a"], extra=["b"])
        s = str(err)
        assert "missing" in s
        assert "unexpected" in s
        assert ";" in s

    def test_raises_and_catches_as_value_error(self):
        try:
            raise ColumnMismatchError(missing=["x"])
        except ValueError as e:
            assert "missing" in str(e)

    def test_missing_preserves_order(self):
        err = ColumnMismatchError(missing=["c", "a", "b"])
        assert err.missing == ["c", "a", "b"]

    def test_extra_preserves_order(self):
        err = ColumnMismatchError(missing=[], extra=["z", "a"])
        assert err.extra == ["z", "a"]


class TestColumnMismatchErrorPickle:
    def test_pickle_round_trip(self):
        err = ColumnMismatchError(missing=["a", "b"], extra=["z"])
        restored = pickle.loads(pickle.dumps(err))
        assert isinstance(restored, ColumnMismatchError)
        assert restored.missing == ["a", "b"]
        assert restored.extra == ["z"]
        assert str(restored) == str(err)
        assert repr(restored) == repr(err)

    def test_pickle_missing_only(self):
        err = ColumnMismatchError(missing=["x"])
        restored = pickle.loads(pickle.dumps(err))
        assert restored.missing == ["x"]
        assert restored.extra == []
        assert str(restored) == str(err)

    def test_pickle_empty(self):
        err = ColumnMismatchError(missing=[])
        restored = pickle.loads(pickle.dumps(err))
        assert restored.missing == []
        assert str(restored) == str(err)


class TestColumnMismatchErrorCopies:
    def test_missing_list_copied(self):
        src = ["a"]
        err = ColumnMismatchError(missing=src)
        src.append("mutated")
        assert err.missing == ["a"]

    def test_extra_list_copied(self):
        src = ["x"]
        err = ColumnMismatchError(missing=[], extra=src)
        src.append("mutated")
        assert err.extra == ["x"]

    def test_tuple_converted_to_list(self):
        err = ColumnMismatchError(missing=("a", "b"), extra=("c",))
        assert err.missing == ["a", "b"]
        assert err.extra == ["c"]
        assert isinstance(err.missing, list)
        assert isinstance(err.extra, list)
