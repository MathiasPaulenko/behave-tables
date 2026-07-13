# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-07-13

### Added

- `find_all_rows(**filters)` — return all rows matching filters (copies)
- `__getitem__` slice support — `table[0:2]` returns list of dict copies
- `__eq__` — compare two wrappers by headers and rows
- `__contains__` — check if a row dict is present in the table
- `to_csv(delimiter, quoting)` — configurable CSV delimiter and quoting level
- `to_json(sort_keys, default)` — sort keys and custom serializer support
- `validate_columns(strict=True)` — detect unexpected columns in addition to missing
- `as_models()` filters extra columns automatically (dataclass and Pydantic)
- `ColumnMismatchError.__repr__` — unambiguous representation with missing and extra
- `[tool.ruff.format]` configuration in `pyproject.toml`
- `make format` target in Makefile
- 78 new edge-case tests (168 total, 100% coverage)

### Changed

- Renamed internal `_mock.py` to `_table_impl.py` (`MockTable` → `SimpleTable`)
- `transpose()` uses top-level import instead of deferred import
- `column()` error message uses `self._table.headings` instead of `self.headers` copy
- `validate_columns()` uses `set(self._table.headings)` instead of `self.headers` copy
- `to_json()` serializes `self.as_dicts()` instead of internal `self._rows` references
- Test helpers moved from `helpers.py` to `conftest.py` as `@pytest.fixture`

### Fixed

- CI Codecov upload: downgraded to `codecov-action@v3` for tokenless upload
- Ruff import sorting issue in `wrapper.py`

## [1.0.0] - 2026-07-13

### Added

- `TableWrapper` class wrapping `behave.model.Table`
- `wrap()` convenience function
- `as_dicts()` — rows as list of dicts (copies)
- `as_models(model)` — rows as Pydantic v2 or dataclass instances
- `column(name)` — extract single column values
- `find_row(**filters)` — find first matching row (returns copy)
- `validate_columns(*expected)` — column validation
- `transpose()` — swap rows and columns
- `to_csv()` — CSV export with `restval` and `extrasaction` handling
- `to_json(indent)` — JSON export with configurable indentation
- `headers` property (returns copy)
- `__iter__`, `__getitem__`, `__len__` for dict-like iteration (all return copies)
- `ColumnMismatchError` exception with `missing` and `extra` attributes
- `TableLike` protocol exported in public API
- Zero required dependencies (pydantic optional)

### Changed

- All public methods return copies of internal data to prevent mutation leaks
- `to_csv()` handles missing values and extra keys gracefully
- `to_json()` accepts `indent: int | None` (supports compact output)
- `is_pydantic_model()` catches `TypeError` in addition to `ImportError`
- `transpose()` uses `row.get(header, "")` instead of `row[header]`
- Relative import in `transpose()` instead of absolute
- Google-style docstrings with `Args`, `Returns`, `Raises` throughout
- Development status changed to Production/Stable

### Fixed

- Mutable leak in `find_row()`, `__iter__`, `__getitem__` (returned internal references)
- `to_csv()` crash on missing values or extra keys in rows
- `is_pydantic_model()` crash on non-class input (`TypeError`)
- `ColumnMismatchError` empty message when no missing or extra columns
- Incorrect type hint in `to_json(indent: int)` (should be `int | None`)
- Unnecessary list copy in `column()` membership check
- Dead code: removed duplicate `conftest.py`

## [0.1.0] - 2026-07-13

### Added

- Initial release
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
