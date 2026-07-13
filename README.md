# behave-tables

Polished API for Behave Data Tables.

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

| Method | Returns | Description |
|---|---|---|
| `as_dicts()` | `list[dict[str, str]]` | All rows as dicts |
| `as_models(model)` | `list[Model]` | Rows as Pydantic or dataclass instances |
| `column(name)` | `list[str]` | Values for a single column |
| `find_row(**filters)` | `dict[str, str] \| None` | First row matching all filters |
| `validate_columns(*expected)` | `None` | Raise `ColumnMismatchError` if columns missing |
| `transpose()` | `TableWrapper` | New wrapper with rows and columns swapped |
| `to_csv()` | `str` | CSV string |
| `to_json()` | `str` | JSON string |
| `headers` | `list[str]` | Column names |
| `__iter__` | `Iterator[dict]` | Iterate rows as dicts |
| `__getitem__(i)` | `dict[str, str]` | Row at index as dict |
| `__len__` | `int` | Number of rows |

## Zero dependencies

`behave-tables` has no required dependencies. `as_models()` works with stdlib `dataclasses` out of the box. Install `pydantic` optionally for validation.

## License

MIT
