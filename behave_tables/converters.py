"""Type conversion logic for as_models()."""

from __future__ import annotations

import dataclasses
from typing import Any


def is_pydantic_model(model: type) -> bool:
    """Check if a class is a Pydantic v2 BaseModel subclass."""
    try:
        from pydantic import BaseModel

        return isinstance(model, type) and issubclass(model, BaseModel)
    except ImportError:
        return False


def is_dataclass_type(model: type) -> bool:
    """Check if a class is a dataclass."""
    return isinstance(model, type) and dataclasses.is_dataclass(model)


def convert_row_to_model(row: dict[str, str], model: type) -> Any:
    """Convert a dict row to a model instance.

    Detects Pydantic v2 BaseModel or stdlib dataclass automatically.
    """
    if is_pydantic_model(model):
        return model(**row)
    if is_dataclass_type(model):
        return model(**row)
    raise TypeError(
        f"model must be a Pydantic BaseModel or dataclass, got {model!r}"
    )
