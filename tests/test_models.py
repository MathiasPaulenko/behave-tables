"""Tests for as_models() with dataclasses and Pydantic."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from behave_tables import wrap


@dataclass
class UserDC:
    name: str
    age: int


@dataclass
class UserDCWithDefaults:
    name: str | None = None
    age: int | None = None


class TestAsModelsDataclass:
    def test_basic(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        users = wt.as_models(UserDC)
        assert len(users) == 2
        assert users[0].name == "Alice"
        assert users[1].name == "Bob"

    def test_empty_table(self, make_table):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        assert wt.as_models(UserDC) == []

    def test_type_error_on_non_model(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(TypeError, match="Pydantic BaseModel or dataclass"):
            wt.as_models(dict)

    def test_extra_columns_ignored(self, make_table):
        table = make_table(["name", "age", "extra"], [["Alice", "30", "ignored"]])
        wt = wrap(table)
        users = wt.as_models(UserDC)
        assert users[0].name == "Alice"
        assert users[0].age == "30"


class TestAsModelsPydantic:
    def test_basic(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class UserPyd(BaseModel):
            name: str
            age: int

        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        users = wt.as_models(UserPyd)
        assert len(users) == 2
        assert users[0].name == "Alice"
        assert users[0].age == 30
        assert isinstance(users[0], BaseModel)

    def test_pydantic_validation_error(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, ValidationError

        class StrictUser(BaseModel):
            name: str
            age: int

        table = make_table(["name", "age"], [["Alice", "not_a_number"]])
        wt = wrap(table)
        with pytest.raises(ValidationError):
            wt.as_models(StrictUser)

    def test_pydantic_extra_columns_ignored(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class UserPyd(BaseModel):
            name: str
            age: int

        table = make_table(["name", "age", "extra"], [["Alice", "30", "ignored"]])
        wt = wrap(table)
        users = wt.as_models(UserPyd)
        assert users[0].name == "Alice"
        assert users[0].age == 30


class TestAsModelsEdgeCases:
    def test_dataclass_missing_column(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        users = wt.as_models(UserDCWithDefaults)
        assert users[0].name == "Alice"
        assert users[0].age is None

    def test_dataclass_all_extra_columns(self, make_table):
        table = make_table(["extra1", "extra2"], [["x", "y"]])
        wt = wrap(table)
        users = wt.as_models(UserDCWithDefaults)
        assert users[0].name is None
        assert users[0].age is None

    def test_dataclass_without_defaults_missing_raises(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(TypeError):
            wt.as_models(UserDC)

    def test_dataclass_single_row(self, make_table):
        table = make_table(["name", "age"], [["Alice", "30"]])
        wt = wrap(table)
        users = wt.as_models(UserDC)
        assert len(users) == 1

    def test_type_error_on_none(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(TypeError, match="Pydantic BaseModel or dataclass"):
            wt.as_models(None)

    def test_type_error_on_int(self, make_table):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(TypeError, match="Pydantic BaseModel or dataclass"):
            wt.as_models(42)

    def test_pydantic_missing_column_raises(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, ValidationError

        class StrictUser(BaseModel):
            name: str
            age: int

        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(ValidationError):
            wt.as_models(StrictUser)

    def test_pydantic_extra_only(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, ValidationError

        class UserPyd(BaseModel):
            name: str
            age: int

        table = make_table(["extra"], [["ignored"]])
        wt = wrap(table)
        with pytest.raises(ValidationError):
            wt.as_models(UserPyd)

    def test_pydantic_empty_table(self, make_table):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class UserPyd(BaseModel):
            name: str

        table = make_table(["name"], [])
        wt = wrap(table)
        assert wt.as_models(UserPyd) == []
