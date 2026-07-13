# behave-tables

[![PyPI version](https://img.shields.io/pypi/v/behave-tables.svg)](https://pypi.org/project/behave-tables/)
[![Python versions](https://img.shields.io/pypi/pyversions/behave-tables.svg)](https://pypi.org/project/behave-tables/)
[![CI status](https://github.com/MathiasPaulenko/behave-tables/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-tables/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/MathiasPaulenko/behave-tables)
[![License](https://img.shields.io/pypi/l/behave-tables.svg)](https://github.com/MathiasPaulenko/behave-tables/blob/main/LICENSE)
[![Pydantic](https://img.shields.io/badge/pydantic-optional-blue)](https://pypi.org/project/pydantic/)

> Polished API for Behave Data Tables — convert to dicts, Pydantic models, CSV, JSON & JSON Lines.
> Zero deps · Type-safe · Python 3.11+ · 100% test coverage

---

## Why?

Behave's `Table` requires manual iteration:

```python
# Without behave-tables — repetitive, error-prone
for row in context.table.rows:
    name = row["name"]
    age = row["age"]
    # No dicts, no models, no CSV, no JSON...
```

Every project reimplements the same helpers. **behave-tables** fixes this with a single `wrap()` call.

---

## Install

```bash
pip install behave-tables

# Optional: pydantic for as_models() with validation & type coercion
pip install behave-tables[pydantic]
```

---

## Quick start

```python
from behave_tables import TableWrapper, wrap

@then("the users should be")
def step_impl(context):
    table = wrap(context.table)

    # Convert to dicts
    users = table.as_dicts()
    # [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    # Convert to models (Pydantic v2 or dataclass)
    users = table.as_models(User)

    # Extract a single column
    names = table.column("name")  # ["Alice", "Bob"]

    # Find the first matching row
    alice = table.find_row(name="Alice")  # {"name": "Alice", "age": "30"}

    # Find all matching rows
    thirty_somethings = table.find_all_rows(age="30")

    # Validate columns (strict mode detects extras too)
    table.validate_columns("name", "age", strict=True)

    # Export
    csv_str = table.to_csv(delimiter=";")
    json_str = table.to_json(sort_keys=True)

    # Transpose rows and columns
    transposed = table.transpose()

    # Transform
    selected = table.select("name", "age")
    cleaned = table.drop("internal_id")
    renamed = table.rename_columns({"name": "full_name"})
    sorted_wt = table.sort("age", reverse=True)
    deduped = table.distinct()

    # Query
    cities = table.unique("city")
    count = table.count(age="30")
    first = table.first()
    last = table.last()

    # Export & import (round-trip)
    jsonl = table.to_jsonl()
    restored = TableWrapper.from_csv(table.to_csv())
    restored = TableWrapper.from_json(table.to_json())

    # Iterate, index, and measure
    for row in table:
        print(row["name"])

    table[0]     # {"name": "Alice", "age": "30"}
    table[0:2]   # [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    len(table)   # 2

    # Compare and check membership
    assert table == wrap(other_table)
    assert {"name": "Alice", "age": "30"} in table
```

---

## API

### `wrap(table)`

Wrap a `behave.model.Table` (or any table-like object) with `TableWrapper`.

### `TableWrapper`

| Method | Returns | Description |
| :--- | :--- | :--- |
| `as_dicts()` | `list[dict[str, str]]` | All rows as dicts (copies) |
| `as_models(model)` | `list[Model]` | Rows as Pydantic v2 or dataclass instances |
| `column(name)` | `list[str]` | Values for a single column |
| `find_row(**filters)` | `dict[str, str] \| None` | First row matching all filters |
| `find_all_rows(**filters)` | `list[dict[str, str]]` | All rows matching all filters (copies) |
| `validate_columns(*expected, strict=False)` | `None` | Raise `ColumnMismatchError` if columns missing or unexpected |
| `transpose()` | `TableWrapper` | New wrapper with rows and columns swapped |
| `to_csv(delimiter=",", quoting=QUOTE_MINIMAL)` | `str` | CSV string with configurable delimiter and quoting |
| `to_json(indent=2, sort_keys=False, default=None)` | `str` | JSON string (list of objects) |
| `to_jsonl()` | `str` | JSON Lines string (one object per line) |
| `select(*columns)` | `TableWrapper` | New wrapper with only the specified columns |
| `drop(*columns)` | `TableWrapper` | New wrapper without the specified columns |
| `rename_columns(mapping)` | `TableWrapper` | New wrapper with renamed columns |
| `sort(key, reverse=False)` | `TableWrapper` | New wrapper with rows sorted by column or callable |
| `unique(column)` | `list[str]` | Unique values for a column (first-seen order) |
| `distinct()` | `TableWrapper` | New wrapper with duplicate rows removed |
| `count(**filters)` | `int` | Count rows matching all filters |
| `first()` | `dict[str, str] \| None` | First row as dict copy, or `None` if empty |
| `last()` | `dict[str, str] \| None` | Last row as dict copy, or `None` if empty |
| `from_csv(csv_string, delimiter=",")` | `TableWrapper` | Classmethod: create wrapper from CSV string |
| `from_json(json_string)` | `TableWrapper` | Classmethod: create wrapper from JSON string |
| `headers` | `list[str]` | Column names |
| `__iter__` | `Iterator[dict]` | Iterate rows as dicts |
| `__getitem__(i)` | `dict[str, str] \| list[dict[str, str]]` | Row at index as dict, or list of dicts for a slice |
| `__len__` | `int` | Number of rows |
| `__eq__` | `bool` | Compare by headers and rows |
| `__contains__` | `bool` | Check if a row dict is present |
| `__repr__` | `str` | Unambiguous representation |

### `ColumnMismatchError`

Raised by `validate_columns()` when expected columns are missing or unexpected columns are found. Subclass of `ValueError`.

```python
from behave_tables import wrap, ColumnMismatchError

table = wrap(context.table)
try:
    table.validate_columns("name", "email")
except ColumnMismatchError as e:
    print(e.missing)  # ["email"]

# Strict mode: also detects unexpected columns
try:
    table.validate_columns("name", strict=True)
except ColumnMismatchError as e:
    print(e.missing)  # []
    print(e.extra)   # ["age", "email"]
```

---

## Examples

### With dataclasses

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int

@then("the users should be")
def step_impl(context):
    users = wrap(context.table).as_models(User)
    assert users[0].name == "Alice"
```

### With Pydantic v2

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

@then("the users should be")
def step_impl(context):
    users = wrap(context.table).as_models(User)
    # Pydantic validates and coerces types automatically
    assert users[0].age == 30  # int, not str
```

### Validate columns

```python
@then("the user list should be")
def step_impl(context):
    table = wrap(context.table)
    table.validate_columns("name", "email", "role")
    # Proceed with confidence that columns exist

# Strict mode: ensure no extra columns
@then("the user list has exactly these columns")
def step_impl(context):
    table = wrap(context.table)
    table.validate_columns("name", "email", strict=True)
```

### Transpose

```python
@then("the data should be")
def step_impl(context):
    table = wrap(context.table)
    transposed = table.transpose()
    # Original headers become the first column ("_column")
    # Original row indices become the new headers ("0", "1", ...)
```

### Find rows

```python
@then("users aged 30 should exist")
def step_impl(context):
    table = wrap(context.table)
    users = table.find_all_rows(age="30")
    assert len(users) == 2

    # Find first match
    alice = table.find_row(name="Alice")
```

### Compare and check membership

```python
@then("the table matches expected data")
def step_impl(context):
    table = wrap(context.table)
    other = wrap(other_table)
    assert table == other

    # Check if a row exists
    assert {"name": "Alice", "age": "30"} in table
```

### Export & import

```python
@then("the report is generated")
def step_impl(context):
    table = wrap(context.table)
    csv_output = table.to_csv(delimiter=";")
    json_output = table.to_json(indent=4, sort_keys=True)
    jsonl_output = table.to_jsonl()  # one JSON object per line

# Round-trip: export then re-import
restored = TableWrapper.from_csv(csv_output)
restored = TableWrapper.from_json(json_output)
```

### Transform

```python
@then("the user names are extracted")
def step_impl(context):
    table = wrap(context.table)
    names_only = table.select("name")
    without_id = table.drop("internal_id")
    renamed = table.rename_columns({"name": "full_name"})
    sorted_by_age = table.sort("age", reverse=True)
    deduped = table.distinct()
```

### Query

```python
@then("the statistics are computed")
def step_impl(context):
    table = wrap(context.table)
    cities = table.unique("city")
    count = table.count(age="30")
    first_user = table.first()
    last_user = table.last()
```

---

## Design principles

- **Zero dependencies** — no required packages. `as_models()` works with stdlib `dataclasses` out of the box. Install `pydantic` optionally for validation and type coercion.
- **Immutable returns** — all public methods return copies of internal data. Modifying results never affects the wrapper state.
- **Type-safe** — ships with `py.typed` (PEP 561) for full type checker support (mypy, pyright).
- **Defensive by default** — `to_csv()` handles missing values and extra keys gracefully. `is_pydantic_model()` won't crash on non-class input.
- **Protocol-based** — `TableLike` protocol accepts any object with `headings` and `rows`, not just `behave.model.Table`.

---

## Development

```bash
make dev            # install with dev dependencies
make test           # run tests
make test-cov       # run tests with coverage
make lint           # check code style
make lint-fix       # auto-fix lint issues
make format         # format code with ruff
make format-check   # verify code is formatted
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

MIT
