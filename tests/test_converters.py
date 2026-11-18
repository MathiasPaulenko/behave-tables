"""Tests for converters module."""

from __future__ import annotations

from dataclasses import KW_ONLY, InitVar, dataclass, field
from typing import ClassVar
from unittest.mock import patch

import pytest

from behave_tables.converters import (
    _model_fields,
    convert_row_to_model,
    is_dataclass_type,
    is_pydantic_model,
)


@dataclass
class Sample:
    name: str
    age: int


@dataclass
class SampleWithDefaults:
    name: str | None = None
    age: int | None = None


class TestIsPydanticModel:
    def test_with_pydantic_installed(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class MyModel(BaseModel):
            pass

        assert is_pydantic_model(MyModel) is True

    def test_non_model_class(self):
        assert is_pydantic_model(dict) is False
        assert is_pydantic_model(str) is False

    def test_non_type_returns_false(self):
        assert is_pydantic_model(42) is False
        assert is_pydantic_model("not_a_class") is False

    def test_import_error_returns_false(self):
        with patch("builtins.__import__", side_effect=ImportError):
            assert is_pydantic_model(dict) is False


class TestIsDataclassType:
    def test_dataclass(self):
        assert is_dataclass_type(Sample) is True

    def test_non_dataclass(self):
        assert is_dataclass_type(dict) is False
        assert is_dataclass_type(42) is False


class TestConvertRowToModel:
    def test_dataclass_conversion(self):
        result = convert_row_to_model({"name": "Alice", "age": "30"}, Sample)
        assert result.name == "Alice"
        assert result.age == "30"

    def test_dataclass_extra_columns_filtered(self):
        result = convert_row_to_model({"name": "Alice", "age": "30", "extra": "ignored"}, Sample)
        assert result.name == "Alice"
        assert result.age == "30"

    def test_non_model_raises_type_error(self):
        with pytest.raises(TypeError, match="Pydantic BaseModel or dataclass"):
            convert_row_to_model({"x": "1"}, dict)


class TestModelFields:
    def test_dataclass_fields(self):
        fields = _model_fields(Sample)
        assert fields == {"name", "age"}

    def test_non_model_returns_none(self):
        assert _model_fields(dict) is None
        assert _model_fields(str) is None


class TestConvertRowToModelEdgeCases:
    def test_dataclass_with_missing_field(self):
        result = convert_row_to_model({"name": "Alice"}, SampleWithDefaults)
        assert result.name == "Alice"
        assert result.age is None

    def test_dataclass_empty_row(self):
        result = convert_row_to_model({}, SampleWithDefaults)
        assert result.name is None
        assert result.age is None

    def test_dataclass_all_extra_columns(self):
        result = convert_row_to_model({"extra1": "x", "extra2": "y"}, SampleWithDefaults)
        assert result.name is None
        assert result.age is None

    def test_dataclass_without_defaults_missing_field_raises(self):
        with pytest.raises(TypeError):
            convert_row_to_model({"name": "Alice"}, Sample)

    def test_pydantic_conversion(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str
            age: int

        result = convert_row_to_model({"name": "Alice", "age": "30"}, MyModel)
        assert result.name == "Alice"
        assert result.age == 30

    def test_pydantic_extra_columns_filtered(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str

        result = convert_row_to_model({"name": "Alice", "extra": "ignored"}, MyModel)
        assert result.name == "Alice"

    def test_pydantic_model_fields(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str
            age: int

        fields = _model_fields(MyModel)
        assert fields == {"name", "age"}


class TestIsPydanticModelEdgeCases:
    def test_none_returns_false(self):
        assert is_pydantic_model(None) is False

    def test_list_returns_false(self):
        assert is_pydantic_model([]) is False

    def test_type_error_returns_false(self):
        with patch("builtins.__import__", side_effect=TypeError):
            assert is_pydantic_model(dict) is False


class TestIsDataclassTypeEdgeCases:
    def test_none_returns_false(self):
        assert is_dataclass_type(None) is False

    def test_string_returns_false(self):
        assert is_dataclass_type("not_a_class") is False

    def test_instance_not_type_returns_false(self):
        assert is_dataclass_type(Sample("a", 1)) is False


class TestModelFieldsInitFilter:
    def test_init_false_field_excluded(self):
        @dataclass
        class WithComputed:
            name: str
            computed: str = field(init=False, default="derived")

        assert _model_fields(WithComputed) == {"name"}

    def test_initvar_included(self):
        @dataclass
        class WithInitVar:
            name: str
            token: InitVar = "default"

        assert _model_fields(WithInitVar) == {"name", "token"}

    def test_init_false_column_not_passed_to_model(self):
        @dataclass
        class WithComputed:
            name: str
            computed: str = field(init=False, default="derived")

        result = convert_row_to_model({"name": "Alice", "computed": "ignored"}, WithComputed)
        assert result.name == "Alice"
        assert result.computed == "derived"

    def test_classvar_excluded(self):
        @dataclass
        class WithClassVar:
            name: str
            KIND: ClassVar[str] = "user"

        assert _model_fields(WithClassVar) == {"name"}

    def test_classvar_column_not_passed_to_model(self):
        @dataclass
        class WithClassVar:
            name: str
            KIND: ClassVar[str] = "user"

        result = convert_row_to_model({"name": "Alice", "KIND": "admin"}, WithClassVar)
        assert result.name == "Alice"
        assert result.KIND == "user"

    def test_kw_only_marker_excluded(self):
        @dataclass
        class WithKwOnly:
            name: str
            _: KW_ONLY
            age: str = "0"

        assert _model_fields(WithKwOnly) == {"name", "age"}
        result = convert_row_to_model({"name": "Alice", "age": "30", "_": "x"}, WithKwOnly)
        assert result.age == "30"


class TestModelFieldsPydanticAliases:
    def test_alias_included(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, Field

        class M(BaseModel):
            name: str = Field(alias="user_name")

        fields = _model_fields(M)
        assert "name" in fields
        assert "user_name" in fields

    def test_validation_alias_str_included(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, Field

        class M(BaseModel):
            name: str = Field(validation_alias="user_name")

        assert "user_name" in _model_fields(M)

    def test_alias_choices_included(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, Field
        from pydantic.aliases import AliasChoices

        class M(BaseModel):
            city: str = Field(validation_alias=AliasChoices("town", "city"))

        fields = _model_fields(M)
        assert {"city", "town"} <= fields

    def test_convert_row_with_alias_column(self):
        pytest.importorskip("pydantic")
        from pydantic import BaseModel, Field

        class M(BaseModel):
            name: str = Field(alias="user_name")

        result = convert_row_to_model({"user_name": "Alice"}, M)
        assert result.name == "Alice"
