# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed

- `wrap()` raises a clear `TypeError` for inputs lacking `headings`/`rows`
  (e.g. `None`, ints, strings, dicts) instead of leaking `AttributeError`
- `wrap()` accepts a `TableWrapper` directly (it now satisfies the
  `TableLike` protocol via `headings`/`rows` properties)
- Headings are snapshotted at construction: mutating the source table's
  headings afterwards no longer desynchronizes the wrapper
- Row extraction now supports positional `list`/`tuple` rows and fills
  missing cells with `""`; every row is normalized to the table's
  headings regardless of row type (`as_dict`, dict, sequence or
  `__getitem__`), dropping keys that are not headings
- `find_row()`, `find_all_rows()` and `count()` no longer match rows
  when filtering by a key absent from the row (e.g. `bogus=None`), even
  against objects with permissive `__eq__` such as `unittest.mock.ANY`;
  `in`/`__contains__` likewise only accepts real dict rows
- Non-string cell values are coerced to their JSON representation on
  every row path (same rule as `from_json()`), restoring the documented
  `dict[str, str]` invariant and preventing mutable objects from being
  shared between wrapper internals and callers
- `as_models()` works with dataclass fields declared `init=False`
  (previously passed them to the constructor and crashed), ignores
  `ClassVar` and `KW_ONLY` pseudo-fields even when a matching column
  exists, and supports Pydantic `Field(alias=...)`/`AliasChoices`
  (previously filtered out)
- `sort()` raises `TypeError` for non-string, non-callable keys instead
  of `KeyError`, and callable keys can no longer mutate internal rows
- `from_csv()` raises `TypeError` for non-string input (previously
  `None` silently produced an empty table), strips a leading UTF-8 BOM,
  and ignores leading blank lines (previously all data was silently
  discarded when the file started with an empty line)
- `from_json()` raises `TypeError` for non-string input instead of
  leaking `json.loads` errors
- `rename_columns()` raises `TypeError` for non-mapping arguments
  instead of `AttributeError`, and for non-string new column names
  (which produced unreachable columns)
- `validate_columns()` deduplicates repeated missing/extra columns in
  the raised `ColumnMismatchError`
- `ColumnMismatchError` defensively copies `missing`/`extra` and
  survives `pickle` round-trips without corrupting its message
- `select()`, `drop()`, `rename_columns()`, `sort()`, `transpose()`,
  `from_csv()` and `from_json()` preserve subclasses (return
  `type(self)`/`cls` instead of always `TableWrapper`)

## [1.4.0] - 2026-10-05

### Fixed

- `column()` no longer raises `KeyError` on rows missing a value for a valid
  header (e.g. tables built by `from_json()` with heterogeneous objects);
  missing values now return `""`, consistent with `unique()`, `sort()` and
  `to_csv()`
- `from_csv()` fills short rows with `""` instead of `None` and ignores extra
  fields instead of storing them under a `None` key
- `to_csv()` no longer corrupts CRLF characters embedded in cell values
  (uses `lineterminator="\n"` instead of post-processing the output)
- `rename_columns()` raises `ValueError` when the mapping would produce
  duplicate column names (previously caused silent data loss)
- `select()` raises `ValueError` when a column is requested more than once
- `from_json()` coerces non-string values to their JSON representation,
  keeping the `dict[str, str]` row invariant
- `to_json()` `default` parameter is now typed as `Callable | None`
- Release workflow: changelog extraction now matches version headers
  literally (was a broken regex match, producing empty release notes)
- CI: coverage `fail_under` is now actually enforced via `--cov-report=term-missing`
- CI: bumped `codecov-action` to v5

### Changed

- Removed deprecated `License ::` classifier (PEP 639: redundant with
  SPDX `license` field)
- `build` added to dev dependencies so `make build` works on a fresh dev setup
- README: reformatted for ruff 0.16 compatibility

## [1.3.2] - 2026-08-06

### Fixed

- Added author email to `pyproject.toml`

## [1.3.1] - 2026-07-13

### Added

- `py.typed` marker (PEP 561) for full type checker support (mypy, pyright)
- `make format-check` target to verify code is formatted

### Changed

- README: import `TableWrapper` in quick start, document type safety, add `make format-check`
- CONTRIBUTING: add `make format` and `make format-check` to workflow and PR checklist

## [1.3.0] - 2026-07-13

### Fixed

- `sort()` now raises `KeyError` when the column does not exist (was silently sorting with empty strings)
- `from_json()` now validates input types — raises `TypeError` for non-list JSON or non-dict rows

### Changed

- `as_models()` return type is now `list[M]` via `TypeVar` instead of `list[Any]`
- `__hash__` explicitly set to `None` to document unhashable intent
- `convert_row_to_model()` deduplicated — single branch for pydantic and dataclass
- Removed unnecessary `pythonpath` from `pyproject.toml` pytest config
- Module docstring and package description updated to reflect full feature set

### CI/Infra

- Added Python 3.14 to CI matrix
- Added `ruff format --check` to CI pipeline

## [1.2.1] - 2026-07-13

### Fixed

- Ruff lint errors in test_new_methods (E501) and sort method (B023)

## [1.2.0] - 2026-07-13

### Added

- `select(*columns)` — project to a new wrapper with only the specified columns
- `drop(*columns)` — return a new wrapper without the specified columns
- `rename_columns(mapping)` — return a new wrapper with renamed columns
- `sort(key, reverse=False)` — sort rows by column name or callable
- `unique(column)` — unique values for a column, preserving first-seen order
- `distinct()` — remove duplicate rows
- `count(**filters)` — count matching rows without materializing them
- `first()` / `last()` — convenience access to first/last row (or `None`)
- `to_jsonl()` — JSON Lines export (one object per line)
- `TableWrapper.from_csv(csv_string)` — classmethod to create from CSV
- `TableWrapper.from_json(json_string)` — classmethod to create from JSON
- 66 new tests (234 total, 100% coverage)

### Changed

- GitHub Release is now created automatically by CI on tag push

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
