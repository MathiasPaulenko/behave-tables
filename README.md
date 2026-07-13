# behave-tables

[![PyPI version](https://img.shields.io/pypi/v/behave-tables.svg)](https://pypi.org/project/behave-tables/)
[![Python versions](https://img.shields.io/pypi/pyversions/behave-tables.svg)](https://pypi.org/project/behave-tables/)
[![CI status](https://github.com/MathiasPaulenko/behave-tables/actions/workflows/ci.yml/badge.svg)](https://github.com/MathiasPaulenko/behave-tables/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/MathiasPaulenko/behave-tables)
[![License](https://img.shields.io/pypi/l/behave-tables.svg)](https://github.com/MathiasPaulenko/behave-tables/blob/main/LICENSE)
[![Pydantic](https://img.shields.io/badge/pydantic-optional-blue)](https://pypi.org/project/pydantic/)

Polished API for Behave Data Tables — convert to dicts, Pydantic models, CSV & JSON. Zero deps, type-safe, Python 3.11+.

## Why?

Behave's `Table` requires manual iteration: `for row in table.rows: name = row["name"]`. No conversion to dicts, models, CSV, or JSON. Every project reimplements helpers.

## Install

```bash
pip install behave-tables
# Optional: pydantic for as_models() with validation
pip install behave-tables[pydantic]
```

## Quick start

```python
from behave_tables import wrap

# In a step definition
@then("the users should be")
def step_impl(context):
    table = wrap(context.table)

    # As dicts
    users = table.as_dicts()
    # [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

    # As models (Pydantic or dataclass)
    users = table.as_models(User)

    # Column extraction
    names = table.column("name")  # ["Alice", "Bob"]

    # Find first matching row
    alice = table.find_row(name="Alice")  # {"name": "Alice", "age": "30"}

    # Export
    csv_str = table.to_csv()
    json_str = table.to_json()

    # Transpose
    transposed = table.transpose()

    # Iterate as dicts
    for row in table:
        print(row["name"])

    # Index
    table[0]  # {"name": "Alice", "age": "30"}
    len(table)  # 2
```

## API

### `wrap(table)`

Wrap a `behave.model.Table` (or any table-like object) with `TableWrapper`.

### `TableWrapper`

| Method | Returns | Description |
|---|---|---|
| `as_dicts()` | `list[dict[str, str]]` | All rows as dicts (copies) |
| `as_models(model)` | `list[Model]` | Rows as Pydantic v2 or dataclass instances |
| `column(name)` | `list[str]` | Values for a single column |
| `find_row(**filters)` | `dict[str, str] \| None` | First row matching all filters |
| `validate_columns(*expected)` | `None` | Raise `ColumnMismatchError` if columns missing |
| `transpose()` | `TableWrapper` | New wrapper with rows and columns swapped |
| `to_csv()` | `str` | CSV string |
| `to_json(indent=2)` | `str` | JSON string (list of objects) |
| `headers` | `list[str]` | Column names |
| `__iter__` | `Iterator[dict]` | Iterate rows as dicts |
| `__getitem__(i)` | `dict[str, str]` | Row at index as dict |
| `__len__` | `int` | Number of rows |

### `ColumnMismatchError`

Raised by `validate_columns()` when expected columns are missing. Subclass of `ValueError`.

```python
from behave_tables import wrap, ColumnMismatchError

table = wrap(context.table)
try:
    table.validate_columns("name", "email")
except ColumnMismatchError as e:
    print(e.missing)  # ["email"]
```

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

### Export

```python
@then("the report is generated")
def step_impl(context):
    table = wrap(context.table)
    csv_output = table.to_csv()
    json_output = table.to_json(indent=4)
```

## Zero dependencies

`behave-tables` has no required dependencies. `as_models()` works with stdlib `dataclasses` out of the box. Install `pydantic` optionally for validation and type coercion.

## Development

```bash
make dev        # install with dev dependencies
make test       # run tests
make test-cov   # run tests with coverage
make lint       # check code style
make lint-fix   # auto-fix lint issues
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

MIT
