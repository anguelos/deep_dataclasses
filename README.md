# deep_dataclasses

[![Tests](https://img.shields.io/github/actions/workflow/status/anguelos/deep_dataclasses/tests.yml?label=tests)](https://github.com/anguelos/deep_dataclasses/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/anguelos/deep_dataclasses/badges/coverage.json)](https://github.com/anguelos/deep_dataclasses/actions/workflows/tests.yml)
[![Docs](https://readthedocs.org/projects/deep-dataclasses/badge/?version=latest)](https://deep-dataclasses.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/deep_dataclasses)](https://pypi.org/project/deep_dataclasses/)
[![Python](https://img.shields.io/pypi/pyversions/deep_dataclasses)](https://pypi.org/project/deep_dataclasses/)
[![License](https://img.shields.io/github/license/anguelos/deep_dataclasses)](https://github.com/anguelos/deep_dataclasses/blob/main/LICENSE)
[![Size](https://img.shields.io/github/repo-size/anguelos/deep_dataclasses)](https://github.com/anguelos/deep_dataclasses)


> Define nested dataclass hierarchies as clean, readable schemas — no boilerplate, no dependencies.

---

## The Problem

Python's `@dataclass` requires you to define each level of a nested hierarchy separately, then wire them together manually. Each inner class name must appear three times: once in the class definition, once as the field type hint, and once in `field(default_factory=...)`:

```python
from dataclasses import dataclass, asdict, field

@dataclass
class NestedParent:
    @dataclass
    class Child:
        @dataclass
        class GrandChild:
            grandchild_str: str = "grandchild1"
            grandchild_num: int = 1

        grandchild: GrandChild = field(default_factory=GrandChild)
        child_str: str = "child"

    child: Child = field(default_factory=Child)
    parent_str: str = "parent"
```

And even after all that boilerplate, the asdict round-trip is broken:

```python
NestedParent(**asdict(NestedParent())) == NestedParent()  # False
```

This is because `asdict` serialises nested instances to plain dicts, but `@dataclass` does not coerce them back on construction — unlike flat dataclasses where this works naturally.

---

## The Solution

`@deep_dataclass` lets you express the same hierarchy as a natural nested schema. The decorator infers the class name, type hint, and `default_factory` from the nested block — no repetition:

```python
from deep_dataclasses import deep_dataclass

@deep_dataclass(autosnake=True)
class DeepParent:
    class Child:
        class Grandchild:
            grandchild_str: str = "grandchild1"
            grandchild_num: int = 1
        child_str: str = "child"
    parent_str: str = "parent"

print(DeepParent().child.grandchild)
# Grandchild(grandchild_str='grandchild1', grandchild_num=1)
```

The `autosnake=True` option converts PascalCase inner class names to snake_case field names. Without it the field name matches the class name exactly.

---

## Fully Compatible with `dataclasses`

`@deep_dataclass` produces standard dataclass instances — all stdlib tools work as expected, and the asdict round-trip is fixed:

```python
d1 = NestedParent()  # vanilla dataclass hierarchy
d2 = DeepParent()    # deep_dataclass equivalent

asdict(d1) == asdict(d2)        # True — identical structure
DeepParent(**asdict(d2)) == d2  # True — coercion works
NestedParent(**asdict(d1)) == d1  # False — vanilla @dataclass doesn't coerce nested dicts
```

---

## Validation and Config Loading: A poor mans [pydantic](https://pydantic.dev/)

`to_json_schema` exports any `@deep_dataclass` schema for use with third-party validators. Because `@deep_dataclass` coerces nested dicts at construction time, the validate-then-construct pattern works at all depths:

```python
from deep_dataclasses import to_json_schema
import jsonschema, json

raw = json.loads('{"child": {"grandchild": {"grandchild_num": 2}}}')
jsonschema.validate(raw, to_json_schema(DeepParent))  # validate first
cfg = DeepParent(**raw)                               # then construct — fully typed
assert isinstance(cfg.child, DeepParent.child)        # True
```

Validation catches type violations at any nesting depth:

```python
data = asdict(DeepParent())
data['child']['child_str'] = 3                         # inject a type error
jsonschema.validate(data, to_json_schema(DeepParent))  # raises ValidationError
```

```
Failed validating 'type' in schema['properties']['child']['properties']['child_str']:
    {'type': 'string', 'default': 'child'}

On instance['child']['child_str']:
    3
```

---

## Data Modelling with Type Hints

`@deep_dataclass` works with the full range of `typing` annotations. The `@auxiliary` decorator marks an inner class as a type-only helper — it won't become a standalone field, but can be referenced in `Union[...]`, `List[...]`, `Optional[...]`, etc.

```python
from dataclasses import field, asdict
from typing import Literal, List, Union
from deep_dataclasses import deep_dataclass, auxiliary, to_json_schema
import jsonschema

@deep_dataclass
class Config:
    @auxiliary
    class TrainMode:
        lr: float = 0.001
        pseudo_batch_size: int = 32
    @auxiliary
    class TestMode:
        metric: str = "accuracy"
        folds: int = 5
    mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)
    device: Literal["cpu", "cuda"] = "cpu"
    images: List[str] = field(default_factory=list)
```

When constructing from a dict, `@deep_dataclass` selects the `Union` variant whose field names best cover the keys supplied — an exact match is always preferred over a partial one:

```python
cfg_train = Config(mode={"lr": 0.05})           # 'lr' is a TrainMode field
cfg_test  = Config(mode={"metric": "f1"})        # 'metric' is a TestMode field

assert isinstance(cfg_train.mode, Config.TrainMode)
assert isinstance(cfg_test.mode,  Config.TestMode)
assert cfg_train.mode.pseudo_batch_size == 32    # unspecified fields get defaults
```

Schema validation enforces `Literal` values, `Union` structure, and `List` element types:

```python
jsonschema.validate(asdict(Config()), to_json_schema(Config))  # passes

bad = asdict(Config())
bad["device"] = "tpu"                            # not in Literal["cpu", "cuda"]
jsonschema.validate(bad, to_json_schema(Config)) # raises ValidationError
```

---

## Installation

```bash
pip install deep-dataclasses
```

`deep_dataclasses` has **zero mandatory dependencies** — it uses only `re`, `dataclasses`, and `typing` from the standard library. `jsonschema` (used in the examples above) is an optional third-party package needed only if you want schema validation.

---

## Comparison

| Feature | `@dataclass` | `@deep_dataclass` |
|---|---|---|
| Nested hierarchy | Manual, verbose | Inline, readable |
| `field(default_factory=...)` | Required per field | Automatic |
| Nested dict → instance coercion | ❌ | ✅ (recursive, all depths) |
| `Union` variant selection from dict | ❌ | ✅ (best-match by field coverage) |
| `asdict()` / `==` / `__repr__` | ✅ | ✅ |
| `frozen`, `slots`, etc. | ✅ | ✅ (tested) |
| Type validation | ❌ | Exports to jsonschema |
| Mandatory dependencies | stdlib | stdlib only |

---

## Status

Early release. Core functionality is complete with 100% test coverage. API may evolve — feedback welcome on [discuss.python.org](https://discuss.python.org).

## Contributing

Issues and PRs welcome. See the [issue tracker](https://github.com/anguelos/deep_dataclasses/issues) for known TODOs.
