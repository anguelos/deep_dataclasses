# `@deep_dataclass`

```{eval-rst}
.. autofunction:: deep_dataclasses.deep_dataclass
```

---

## Overview

`@deep_dataclass` is a drop-in replacement for `@dataclass` that additionally
promotes nested class definitions into fields automatically.  Instead of declaring
the type, the field name, and the `default_factory` three times for every nested
class, you write the class inline and the decorator does the rest.

**The result is always a fully valid `@dataclass`.**  Every stdlib tool — 
`dataclasses.fields`, `dataclasses.asdict`, `dataclasses.astuple`, `repr`, `==`,
`__hash__`, `frozen`, `slots`, `order`, `kw_only` — works exactly as it does on a
class decorated with plain `@dataclass`.  Third-party libraries that consume
dataclasses ([dacite](https://github.com/konradhalas/dacite), [dataclass-wizard](https://dataclass-wizard.readthedocs.io/), [pydantic dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/), [cattrs](https://catt.rs/), …) are
likewise fully compatible.

---

## Basic syntax

Without `@deep_dataclass`, a two-level hierarchy requires explicit wiring at every
level:

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    @dataclass
    class Optimizer:
        lr: float = 1e-3
        momentum: float = 0.9

    optimizer: Optimizer = field(default_factory=Optimizer)
    epochs: int = 100
```

With `@deep_dataclass` the inner class is picked up automatically:

```python
from deep_dataclasses import deep_dataclass

@deep_dataclass
class Config:
    class Optimizer:
        lr: float = 1e-3
        momentum: float = 0.9

    epochs: int = 100
```

Both produce an identical dataclass.  The inner `Optimizer` class is also
processed by `@deep_dataclass`, so it too is a valid dataclass and can itself
contain further nested classes.

---

## Differences from plain `@dataclass`

| Behaviour | `@dataclass` | `@deep_dataclass` |
|---|---|---|
| Nested class → field | Manual (3× repetition) | Automatic |
| Mutable defaults (`[]`, `{}`, `set()`) | `ValueError` | Auto-wrapped with `field(default_factory=...)` |
| `asdict` round-trip | Broken for nested dicts | Fixed (coerces dicts on construction) |
| Inner class accessible as attribute | Not guaranteed | Always, even after promotion to a field |
| `@dataclass` kwargs (`frozen`, `slots`, …) | ✅ | ✅ forwarded verbatim |
| stdlib / third-party compatibility | ✅ | ✅ (produces a standard dataclass) |

One important difference: `@deep_dataclass` injects a `__post_init__` that coerces
dict arguments to their declared types (see [Dict coercion](#dict-coercion)).  If
you define your own `__post_init__`, it is preserved and called *after* coercion.

---

## `autosnake` — PascalCase fields to snake_case

By default the field name on the outer class matches the inner class name exactly:

```python
@deep_dataclass
class Model:
    class TransformerEncoder:
        num_layers: int = 6

m = Model()
m.TransformerEncoder.num_layers   # 6
```

With `autosnake=True`, the field name is converted to snake_case while the
PascalCase name is kept as a class attribute alias, so both spellings work:

```python
@deep_dataclass(autosnake=True)
class Model:
    class TransformerEncoder:
        num_layers: int = 6

m = Model()
m.transformer_encoder.num_layers  # 6  ← snake_case field
m.TransformerEncoder.num_layers   # 6  ← PascalCase alias (also works)
```

The alias means that `eval(repr(m))` round-trips correctly regardless of which
spelling appears in `repr`.

`autosnake` is applied recursively, so inner-of-inner class names are also
converted.

---

## Default values

### Primitive and immutable defaults

Primitives (`int`, `str`, `float`, `bool`, `None`), tuples, and frozensets can be
assigned directly as defaults — they are immutable and safe to share between
instances:

```python
@deep_dataclass
class Config:
    lr: float = 1e-3
    tag: str = "baseline"
    device: str = "cpu"
    coords: tuple = (0, 0)
    allowed_ids: frozenset = frozenset([1, 2, 3])
```

### Mutable collection defaults

Plain `@dataclass` raises `ValueError` if you assign a `list`, `dict`, or `set`
directly as a default.  `@deep_dataclass` wraps them automatically:

```python
@deep_dataclass
class Config:
    tags: list = []               # → field(default_factory=list)
    meta: dict = {}               # → field(default_factory=dict)
    ids: set = set()              # → field(default_factory=set)
    scores: list = [1, 2, 3]     # → field(default_factory=lambda: [1, 2, 3])
    mapping: dict = {'k': 'v'}   # → field(default_factory=lambda: {'k': 'v'})
```

Each instance receives its own independent copy — the usual shared-mutable-default
bug does not apply.

Elements of non-empty collection defaults must be primitive types (`int`, `str`,
`float`, `bool`, `None`).  Non-primitive elements raise `TypeError` at decoration
time:

```python
@deep_dataclass
class Bad:
    items: list = [object()]   # TypeError at decoration time
```

If you need a non-primitive default, use `field(default_factory=...)` explicitly:

```python
from dataclasses import field

@deep_dataclass
class Config:
    plugins: list = field(default_factory=list)
```

### Typed collection defaults

For typed fields such as `List[Plugin]`, always use `field(default_factory=...)`:

```python
from typing import List
from dataclasses import field
from deep_dataclasses import deep_dataclass, auxiliary

@deep_dataclass
class Pipeline:
    @auxiliary
    class Plugin:
        name: str = ""
        enabled: bool = True

    plugins: List[Plugin] = field(default_factory=list)
```

---

## Dict coercion

When a `@deep_dataclass` is constructed with a plain `dict` where a typed
dataclass field is expected, the dict is automatically coerced to the correct type.
This is what makes the `asdict` round-trip work:

```python
cfg = Config(Optimizer={"lr": 0.01})
isinstance(cfg.Optimizer, Config.Optimizer)  # True
```

Coercion is **recursive** and works through:

| Field type | Coercion behaviour |
|---|---|
| `SomeDataclass` | `dict` → `SomeDataclass(**dict)` |
| `Optional[T]` | coerces the inner type; passes `None` through |
| `List[T]` | each list element coerced to `T` |
| `Tuple[T1, T2, …]` | each element coerced to its declared type |
| `Tuple[T, …]` | all elements coerced to `T` |
| `Dict[K, V]` | each value coerced to `V` |
| `Set[T]` / `FrozenSet[T]` | each element coerced to `T` |
| `Union[A, B, …]` | best-match variant selected (see below) |

Coercion only touches `dict` values that correspond to a dataclass type.
Non-dataclass fields (`int`, `str`, `List[str]`, …) are passed through unchanged.

To disable coercion entirely, pass `coerce_dicts=False`:

```python
@deep_dataclass(coerce_dicts=False)
class Config:
    class Optimizer:
        lr: float = 1e-3
```

Note: `coerce_dicts=True` (the default) is incompatible with `init=False`.

### `@dataclass` compatibility note

Dict coercion works with plain `@dataclass` fields too.  Any field typed as a
dataclass (standard or deep) will have its dict values coerced as long as the
*outer* class is decorated with `@deep_dataclass`.

---

## Union best-match coercion

When a field is typed as `Union[A, B, ...]` and a `dict` is supplied, 
`@deep_dataclass` selects the variant whose declared field names best cover the
keys in the dict.  The algorithm:

1. For each dataclass variant in the union, count how many of the dict's keys are
   valid field names.
2. Reject any variant that has a key in the dict that it does not declare.
3. Among the remaining candidates, pick the one with the fewest *unfilled* fields
   (i.e. the closest match).  An exact match — where every field in the variant is
   supplied — always wins.

```python
from typing import Union
from dataclasses import field
from deep_dataclasses import deep_dataclass, auxiliary

@deep_dataclass
class Config:
    @auxiliary
    class TrainMode:
        lr: float = 1e-3
        pseudo_batch_size: int = 32

    @auxiliary
    class TestMode:
        metric: str = "accuracy"
        folds: int = 5

    mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)

cfg = Config(mode={"lr": 0.05})          # 'lr' is only in TrainMode
isinstance(cfg.mode, Config.TrainMode)   # True

cfg = Config(mode={"metric": "f1"})      # 'metric' is only in TestMode
isinstance(cfg.mode, Config.TestMode)    # True
```

Non-dataclass union variants (`str`, `int`, …) are not considered for matching;
if no dataclass variant matches, the value is passed through unchanged.

---

## The `@auxiliary` decorator

By default every inner class becomes a field on the outer class.  `@auxiliary`
marks a class as a *type-only helper* — it is processed into a proper dataclass
and kept accessible as a class attribute, but is **not** promoted to a standalone
field:

```python
from deep_dataclasses import deep_dataclass, auxiliary
from typing import List
from dataclasses import field

@deep_dataclass
class Pipeline:
    @auxiliary
    class Stage:
        name: str = ""
        enabled: bool = True

    stages: List[Stage] = field(default_factory=list)

"Stage" in {f.name for f in dataclasses.fields(Pipeline)}  # False
"stages" in {f.name for f in dataclasses.fields(Pipeline)} # True
```

`@auxiliary` is the right choice whenever an inner class is needed as:

- The element type of a `List[T]` or `Set[T]` field
- One arm of a `Union[A, B]` field
- The value type of a `Dict[K, V]` field

**Inheritance and `@auxiliary`:** The `@auxiliary` marker is *not* inherited.
A subclass of an `@auxiliary` class that is not itself decorated with `@auxiliary`
will be promoted to a field as normal:

```python
@deep_dataclass
class App:
    @auxiliary
    class BaseService:
        host: str = "localhost"
        port: int = 8000

    class WebService(BaseService):    # not @auxiliary — becomes a field
        path: str = "/"

    class ApiService(BaseService):   # not @auxiliary — becomes a field
        version: str = "v1"

app = App()
app.WebService.host   # "localhost"  — inherits from BaseService
app.ApiService.port   # 8000
```

---

## Inheritance

`@deep_dataclass` classes can inherit from other `@deep_dataclass` or plain
`@dataclass` classes.  Fields from the parent are included in the child as with
standard dataclasses:

```python
@deep_dataclass
class Base:
    class Logging:
        level: str = "INFO"
    debug: bool = False

@deep_dataclass
class Child(Base):
    class Model:
        num_layers: int = 6
    name: str = "default"
```

The usual dataclass rule applies: a child cannot declare mandatory (no-default)
fields after a parent that has fields with defaults.  `@deep_dataclass` enforces
this at decoration time with a clear error message.

---

## Passing `@dataclass` keyword arguments

All keyword arguments not recognised by `@deep_dataclass` itself are forwarded
to `dataclasses.dataclass()`:

```python
@deep_dataclass(frozen=True)
class ImmutableConfig:
    lr: float = 1e-3

@deep_dataclass(order=True)
class SortableConfig:
    priority: int = 0

@deep_dataclass(slots=True)   # Python 3.10+
class SlottedConfig:
    x: int = 0
```

Because the result is a standard dataclass, all of these options behave exactly
as documented in the stdlib.
