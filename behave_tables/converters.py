"""Type conversion logic for as_models()."""

from __future__ import annotations

import dataclasses
from typing import Any


def _model_fields(model: type) -> set[str] | None:
    """Return the set of field names accepted by the model.

    For dataclasses, uses ``dataclasses.fields``. For Pydantic v2
    models, uses ``model_fields``. Returns ``None`` if the field set
    cannot be determined, in which case no filtering is applied.

    Args:
        model: A Pydantic ``BaseModel`` subclass or a ``dataclass``.

    Returns:
        A set of field name strings, or ``None``.
    """
    if dataclasses.is_dataclass(model):
        return {f.name for f in dataclasses.fields(model)}
    if hasattr(model, "model_fields"):
        return set(model.model_fields)
    return None


def is_pydantic_model(model: type) -> bool:
    """Check if a class is a Pydantic v2 ``BaseModel`` subclass.

    Args:
        model: Any object to test.

    Returns:
        ``True`` if ``model`` is a Pydantic v2 ``BaseModel`` subclass,
        ``False`` otherwise (including when Pydantic is not installed).
    """
    try:
        from pydantic import BaseModel

        return isinstance(model, type) and issubclass(model, BaseModel)
    except (ImportError, TypeError):
        return False


def is_dataclass_type(model: type) -> bool:
    """Check if a class is a dataclass.

    Args:
        model: Any object to test.

    Returns:
        ``True`` if ``model`` is a dataclass type, ``False`` otherwise.
    """
    return isinstance(model, type) and dataclasses.is_dataclass(model)


def convert_row_to_model(row: dict[str, str], model: type) -> Any:
    """Convert a dict row to a model instance.

    Detects Pydantic v2 ``BaseModel`` or stdlib ``dataclass``
    automatically. Pydantic performs validation and type coercion;
    dataclasses receive string values as-is.

    Only keys that match the model's fields are passed; extra columns
    in the row are silently ignored.

    Args:
        row: A dict mapping column names to string values.
        model: A Pydantic ``BaseModel`` subclass or a ``dataclass``.

    Returns:
        An instance of ``model`` populated with the row data.

    Raises:
        TypeError: If ``model`` is not a Pydantic model or dataclass.
    """
    if is_pydantic_model(model) or is_dataclass_type(model):
        fields = _model_fields(model)
        filtered = {k: v for k, v in row.items() if fields is None or k in fields}
        return model(**filtered)
    raise TypeError(f"model must be a Pydantic BaseModel or dataclass, got {model!r}")
