"""Tests for as_models() with dataclasses and Pydantic."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from helpers import make_table

from behave_tables import wrap


@dataclass
class UserDC:
    name: str
    age: int


class TestAsModelsDataclass:
    def test_basic(self):
        table = make_table(["name", "age"], [["Alice", "30"], ["Bob", "25"]])
        wt = wrap(table)
        users = wt.as_models(UserDC)
        assert len(users) == 2
        assert users[0].name == "Alice"
        assert users[1].name == "Bob"

    def test_empty_table(self):
        table = make_table(["name", "age"], [])
        wt = wrap(table)
        assert wt.as_models(UserDC) == []

    def test_type_error_on_non_model(self):
        table = make_table(["name"], [["Alice"]])
        wt = wrap(table)
        with pytest.raises(TypeError, match="Pydantic BaseModel or dataclass"):
            wt.as_models(dict)

    def test_extra_columns_ignored(self):
        table = make_table(["name", "age", "extra"], [["Alice", "30", "ignored"]])
        wt = wrap(table)
        users = wt.as_models(UserDC)
        assert users[0].name == "Alice"
        assert users[0].age == "30"


class TestAsModelsPydantic:
    def test_basic(self):
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

    def test_pydantic_validation_error(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, ValidationError

        class StrictUser(BaseModel):
            name: str
            age: int

        table = make_table(["name", "age"], [["Alice", "not_a_number"]])
        wt = wrap(table)
        with pytest.raises(ValidationError):
            wt.as_models(StrictUser)

    def test_pydantic_extra_columns_ignored(self):
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
