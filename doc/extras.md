# Extras

`deep_dataclasses.extras` is a submodule for features that are intentionally kept
separate from the core library for one of these reasons:

- **Third-party dependency** — the feature requires a package that is not part of
  the Python standard library, so importing it unconditionally would add a mandatory
  dependency to a library that otherwise has none.
- **Optional behaviour** — the feature is useful but too slow, too opinionated, or
  not self-evident enough to belong in the main decorator.

Install the extras dependencies with:

```bash
pip install deep_dataclasses[extras]
```

---

## `validate_defaults`

```{eval-rst}
.. autofunction:: deep_dataclasses.extras.validate_defaults
```

### Overview

`@validate_defaults` is a class decorator that checks, **at class definition time**,
that the default instance of a dataclass satisfies its own JSON schema.  It is a
safety net for authors of configuration classes: if the defaults you ship are
themselves invalid, the error is raised as soon as the module is imported — not
silently at runtime when a user first constructs the class.

```python
from deep_dataclasses import deep_dataclass
from deep_dataclasses.extras import validate_defaults
from typing import Literal

@validate_defaults
@deep_dataclass
class TrainingConfig:
    device: Literal['cpu', 'cuda'] = 'cpu'   # valid default — passes
    lr: float = 1e-3
```

A bad default is caught immediately:

```python
@validate_defaults           # raises TypeError at import time
@deep_dataclass
class BrokenConfig:
    device: Literal['cpu', 'cuda'] = 'tpu'  # 'tpu' not in the Literal
```

```
TypeError: BrokenConfig default instance failed schema validation:
           'tpu' is not one of ['cpu', 'cuda']
```

### Usage forms

The decorator works with or without parentheses:

```python
@validate_defaults                     # uses all defaults
@validate_defaults()                   # equivalent
@validate_defaults(strict=False)       # relax required-field rules
@validate_defaults(enabled=False)      # unconditionally skip validation
@validate_defaults(enabled=__debug__)  # explicit (this is already the default)
```

### The `strict` parameter

`strict` is forwarded to `to_json_schema`.  When `True` (the default), any field
that has no default value is marked `required` in the generated schema.  When
`False`, all fields are treated as optional in the schema regardless of whether
they have defaults.

For the purpose of validating *defaults* this mostly matters when your class has
`Optional` fields: with `strict=False` the schema accepts a missing key where
`strict=True` would require it to be present (as `null`).

```python
from typing import Optional

@validate_defaults(strict=False)
@deep_dataclass
class Config:
    name: Optional[str] = None    # schema accepts absent key with strict=False
```

### The `enabled` parameter and `-O` optimisation

`enabled` defaults to `__debug__`, the built-in flag that Python sets to `False`
when the interpreter is started with `-O` (`PYTHONOPTIMIZE=1`).  This means:

| invocation | `__debug__` | validation runs? |
|---|---|---|
| `python script.py` | `True` | yes |
| `python -O script.py` | `False` | no |
| `PYTHONOPTIMIZE=1 python script.py` | `False` | no |

The intent is that validation is a development-time check.  In production you
typically run with `-O` to strip `assert` statements and other debug overhead;
`validate_defaults` follows the same convention automatically.

You can override this per-decorator:

```python
@validate_defaults(enabled=True)    # always validate, even under -O
@validate_defaults(enabled=False)   # never validate
```

### The `dataclass_default_can_be_validated` companion

If you want a boolean check rather than a decorator that raises, use the companion
function:

```{eval-rst}
.. autofunction:: deep_dataclasses.extras.dataclass_default_can_be_validated
```

```python
from deep_dataclasses.extras import dataclass_default_can_be_validated

if not dataclass_default_can_be_validated(MyConfig):
    print("warning: MyConfig defaults do not satisfy their own schema")
```

Unlike `validate_defaults`, this function never raises — it returns `False` for
non-dataclasses, missing `jsonschema`, and any validation failure.

### Installation note

Both `validate_defaults` and `dataclass_default_can_be_validated` require
[`jsonschema`](https://python-jsonschema.readthedocs.io/).  If it is not installed:

- `dataclass_default_can_be_validated` silently returns `False`.
- `validate_defaults` raises `ImportError` (unless `enabled=False`).

```bash
pip install deep_dataclasses[extras]
```
