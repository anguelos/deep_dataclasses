# `to_json_schema`

```{eval-rst}
.. autofunction:: deep_dataclasses.to_json_schema
```

---

## Overview

`to_json_schema` converts any `@dataclass` or `@deep_dataclass` class into a
[JSON Schema](https://json-schema.org/) `object` descriptor.  The resulting dict
can be passed directly to any JSON Schema validator.

`to_json_schema` works with **any standard dataclass** — not only classes produced
by `@deep_dataclass`.  If you already have plain `@dataclass` classes, you can
export and validate their schemas without any changes.

---

## Basic usage

```python
import jsonschema
from deep_dataclasses import deep_dataclass, to_json_schema

@deep_dataclass
class Config:
    class Optimizer:
        lr: float = 1e-3
        momentum: float = 0.9
    epochs: int = 100

schema = to_json_schema(Config)
# {'type': 'object',
#  'properties': {
#      'Optimizer': {'type': 'object', 'properties': {...}, ...},
#      'epochs':    {'type': 'integer', 'default': 100}
#  },
#  'additionalProperties': False}

jsonschema.validate({"epochs": 50}, schema)          # passes — Optimizer has a default
jsonschema.validate({"epochs": "fifty"}, schema)     # raises — wrong type
```

---

## Supported types

| Python type | JSON Schema |
|---|---|
| `bool` | `{"type": "boolean"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number"}` |
| `str` | `{"type": "string"}` |
| `None` / `type(None)` | `{"type": "null"}` |
| `typing.Any` | `{}` (no constraint) |
| `List[T]` | `{"type": "array", "items": <T schema>}` |
| `Set[T]` / `FrozenSet[T]` | `{"type": "array", "uniqueItems": true, "items": <T schema>}` |
| `Tuple[T, ...]` | `{"type": "array", "items": <T schema>}` |
| `Tuple[T1, T2, T3]` | fixed-length array with `prefixItems` |
| `Dict[K, V]` | `{"type": "object", "additionalProperties": <V schema>}` |
| `Optional[T]` | `{"anyOf": [<T schema>, {"type": "null"}]}` |
| `Union[A, B, …]` | `{"anyOf": [<A schema>, <B schema>, …]}` |
| `Literal[x, y, …]` | `{"enum": [x, y, …]}` |
| Nested dataclass | Recursed — full object schema inline |

---

## `strict` mode

By default (`strict=False`), only fields that have no default value *and* are not
`Optional` are listed under `"required"`.  This means a partial dict validates
successfully as long as the missing fields have defaults:

```python
schema = to_json_schema(Config)               # strict=False
jsonschema.validate({"epochs": 50}, schema)  # passes — Optimizer has a default
```

With `strict=True`, every field is required unless it is `Optional[T]`:

```python
strict = to_json_schema(Config, strict=True)
jsonschema.validate({"epochs": 50}, strict)
# ValidationError: 'Optimizer' is a required property
```

Use `strict=True` when you want to enforce that callers always provide every field
explicitly, for example in an API boundary or config file validator.

---

## `allow_additional_properties`

By default `"additionalProperties": false` is added to the schema, so any key not
declared as a field is rejected.  Pass `allow_additional_properties=True` to
accept extra keys silently — useful when the dataclass represents a partial view
of a larger document:

```python
open_schema = to_json_schema(Config, allow_additional_properties=True)
jsonschema.validate({"epochs": 10, "experiment_id": "run-42"}, open_schema)
```

---

## Validate-then-construct: a simple Pydantic

The combination of `to_json_schema` and `@deep_dataclass`'s dict coercion gives
you a lightweight validate-then-construct pattern that covers most use cases where
you might otherwise reach for Pydantic:

```python
import json, jsonschema
from deep_dataclasses import deep_dataclass, to_json_schema
from typing import Literal, List
from dataclasses import field

@deep_dataclass
class TrainingRun:
    class Optimizer:
        lr: float = 1e-3
        momentum: float = 0.9
    epochs: int = 100
    device: Literal["cpu", "cuda"] = "cpu"
    tags: List[str] = field(default_factory=list)

schema = to_json_schema(TrainingRun)

# --- load and validate raw data (e.g. from a config file) ---
raw = json.loads(open("run.json").read())
jsonschema.validate(raw, schema)     # raises on bad data — before any construction

# --- construct fully-typed object ---
run = TrainingRun(**raw)
isinstance(run.Optimizer, TrainingRun.Optimizer)  # True — dicts coerced recursively
```

Compared to Pydantic:

| | `to_json_schema` + `@deep_dataclass` | Pydantic |
|---|---|---|
| Validation | At construction (jsonschema) | At construction |
| Type coercion | Dataclass-typed fields only | All fields |
| Schema export | `to_json_schema(cls)` | `Model.model_json_schema()` |
| Dependencies | `jsonschema` (optional) | `pydantic` |
| stdlib compatibility | Full `@dataclass` | Separate `BaseModel` |
| Nested dict coercion | ✅ | ✅ |
| Field validators | ❌ (use `__post_init__`) | ✅ |

The key trade-off: `@deep_dataclass` stays in the stdlib dataclass world — you get
full compatibility with everything that consumes dataclasses, at the cost of no
per-field validators.

---

## `Optional` and `Union` schemas

`Optional[T]` becomes `anyOf: [<T schema>, null]`:

```python
from typing import Optional
from dataclasses import dataclass

@dataclass
class Record:
    name: str
    score: Optional[float] = None

to_json_schema(Record)
# {'type': 'object',
#  'properties': {
#      'name':  {'type': 'string'},
#      'score': {'anyOf': [{'type': 'number'}, {'type': 'null'}], 'default': None}
#  },
#  'required': ['name'],
#  'additionalProperties': False}
```

`Union[A, B]` where both variants are dataclasses becomes `anyOf` with their full
inline schemas, which enables [union best-match coercion](deep_dataclass.md#union-best-match-coercion)
at construction time:

```python
from typing import Union
from dataclasses import field
from deep_dataclasses import deep_dataclass, auxiliary, to_json_schema

@deep_dataclass
class Config:
    @auxiliary
    class TrainMode:
        lr: float = 1e-3
    @auxiliary
    class TestMode:
        metric: str = "accuracy"
    mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)

schema = to_json_schema(Config)
# mode schema: {'anyOf': [{'type': 'object', ...TrainMode...},
#                         {'type': 'object', ...TestMode...}]}
```

---

## Using with plain `@dataclass`

`to_json_schema` works on any standard dataclass.  The only limitation is that
construction will **not** coerce nested dicts — that feature requires
`@deep_dataclass`.  Validation still works correctly:

```python
from dataclasses import dataclass
from deep_dataclasses import to_json_schema
import jsonschema

@dataclass
class Point:
    x: float
    y: float

schema = to_json_schema(Point)
jsonschema.validate({"x": 1.0, "y": 2.0}, schema)   # passes
jsonschema.validate({"x": "bad", "y": 2.0}, schema)  # raises
```

---

## Integration with `validate_defaults`

The [`validate_defaults`](extras.md#validate_defaults) decorator from
`deep_dataclasses.extras` uses `to_json_schema` internally to check that a
class's own default instance satisfies its schema.  This is useful as a
module-load-time sanity check on configuration classes:

```python
from deep_dataclasses import deep_dataclass
from deep_dataclasses.extras import validate_defaults

@validate_defaults
@deep_dataclass
class Config:
    device: Literal["cpu", "cuda"] = "cpu"  # checked at import time
```
