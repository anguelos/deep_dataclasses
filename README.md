# deep_dataclasses

![Coverage](https://img.shields.io/badge/coverage-100%25-success)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> Define nested dataclass hierarchies as clean, readable schemas — no boilerplate.

---

## The Problem

Python's `@dataclass` requires you to define each level of a nested hierarchy separately, then wire them together manually with `field(default_factory=...)`:

```python
@dataclass
class GrandChild:
    grandchild_str: str = "grandchild1"
    grandchild_num: int = 1

@dataclass
class Child:
    grandchild: GrandChild = field(default_factory=GrandChild)
    child_str: str = "child"

@dataclass
class Parent:
    child: Child = field(default_factory=Child)
    parent_str: str = "parent"
```

This is verbose, hard to read at a glance, and the nesting structure is only implicit.

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
from dataclasses import asdict

d1 = Parent()   # vanilla dataclass hierarchy
d2 = DeepParent()  # deep_dataclass equivalent

# Structural equality across different class definitions
asdict(d1) == asdict(d2)          # True

# Round-trip via dict
Parent(**asdict(d1)) == d1        # True
DeepParent(**asdict(d2)) == d2    # True
```

---

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
| Type validation | ❌ | ❌ (by design) |

---

## Relationship to PEP 712

Python 3.13's [PEP 712](https://peps.python.org/pep-0712/) added `field(converter=...)` for per-field coercion. `@deep_dataclass` complements this by handling the structural boilerplate one level up — the class hierarchy itself.

---

## Status

Early release. Core functionality is complete and covered at 100%. API may evolve — feedback welcome on [discuss.python.org](https://discuss.python.org).