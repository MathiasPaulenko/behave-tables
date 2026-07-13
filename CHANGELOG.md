# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-07-13

### Added

- `TableWrapper` class wrapping `behave.model.Table`
- `wrap()` convenience function
- `as_dicts()` — rows as list of dicts
- `as_models(model)` — rows as Pydantic or dataclass instances
- `column(name)` — extract single column values
- `find_row(**filters)` — find first matching row
- `validate_columns(*expected)` — column validation
- `transpose()` — swap rows and columns
- `to_csv()` — CSV export
- `to_json()` — JSON export
- `headers` property
- `__iter__`, `__getitem__`, `__len__` for dict-like iteration
- `ColumnMismatchError` exception
- Zero required dependencies (pydantic optional)
