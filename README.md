# deep_dataclasses


[![Tests](https://img.shields.io/github/actions/workflow/status/anguelos/deep_dataclasses/tests.yml?label=tests)](https://github.com/anguelos/deep_dataclasses/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/anguelos/deep_dataclasses/badges/coverage.json)](https://github.com/anguelos/deep_dataclasses/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/deep_dataclasses)](https://pypi.org/project/deep_dataclasses/)
[![Python](https://img.shields.io/pypi/pyversions/deep_dataclasses)](https://pypi.org/project/deep_dataclasses/)
[![License](https://img.shields.io/github/license/anguelos/deep_dataclasses)](https://github.com/anguelos/deep_dataclasses/blob/main/LICENSE)
[![Size](https://img.shields.io/github/repo-size/anguelos/deep_dataclasses)](https://github.com/anguelos/deep_dataclasses)


> Define nested dataclass hierarchies as clean, readable schemas — no boilerplate.

---

## The Problem

Python's `@dataclass` requires you to define each level of a nested hierarchy separately, then wire them together manually with `field(default_factory=...)`:

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
This is verbose, hard to read at a glance and the nested classnames have to be repeated three-fold

But even worse:
```python
NestedParent(**asdict(NestedParent())) == NestedParent()  #  False
```
Is False which is not the behavior of flat dataclasses.

---

## The Solution

`@deep_dataclass` lets you express the same hierarchy as a natural nested schema:

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
```

The decorator recursively converts nested `class` blocks into proper `@dataclass` types, wiring up `field(default_factory=...)` automatically.

---

## Fully Compatible with `dataclasses`

`@deep_dataclass` produces standard dataclass instances — all stdlib tools work as expected:

```python
d1 = NestedParent()   # vanilla dataclass hierarchy
d2 = DeepParent()  # deep_dataclass equivalent

# Structural equality across different class definitions
asdict(d1) == asdict(d2)          # True

# But DeepParent coerses dicts correctly.
DeepParent(**asdict(d2)) == d2    # True
```
---

## Third party validation via jsonschema

While deep_dataclasses dont validate they provide to_json_schema in order to allow third party validation before instantiation in one line.
While to_json_schema runs equally well on all dataclasses, only flat @dataclass and @deep_dataclass make sense, nested dataclasse dont coerse dicts so there is not much use to it.

```python
from deep_dataclasses import to_json_schema
import jsonschema

data = asdict(DeepParent())
jsonschema.validate(data, to_json_schema(DeepParent))  #  Passes

data['child']['child_str']=3
jsonschema.validate(data, to_json_schema(DeepParent))  #  Raises
```

```
Failed validating 'type' in schema['properties']['child']['properties']['child_str']:
    {'type': 'string', 'default': 'child'}

On instance['child']['child_str']:
    3
```


## Installation

```bash
pip install deep-dataclasses
```

---

## Comparison

| Feature | `@dataclass` | `@deep_dataclass` |
|---|---|---|
| Nested hierarchy | Manual, verbose | Inline, readable |
| `field(default_factory=...)` | Required per field | Automatic |
| `asdict()` / `==` / `__repr__` | ✅ | ✅ |
| `frozen`, `slots`, etc. | ✅ | ✅ (tested) |
| Type validation | ❌ | Exports to jsonschema |

---

## Status

Early release. Core functionality is complete and test covered at 100%. API may evolve — feedback welcome on [discuss.python.org](https://discuss.python.org).

## Contributing
Issues and PRs welcome. See the [issue tracker](https://github.com/anguelos/deep_dataclasses/issues) for known TODOs.