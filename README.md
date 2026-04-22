```python
from deep_dataclasses import deep_dataclass
from dataclasses import dataclass


@dataclass
class GrandChild:
    grandchild_str: str = "grandchild1"
    grandchild_num: int = 1

@dataclass
class Child:
    grandchild: GrandChild = field(default_factory=GrandChild)
    child_str:  str = "child"

@dataclass
class Parent:
    child: Child = field(default_factory=Child)
    parent_str: str   = "parent"


@deep_dataclass
class DeepParent:
    parent_str: str = "parent"
    class Child:
        child_str: str = "child"
        class GrandChild:
            grandchild_str: str = "grandchild1"
            grandchild_num: int = 1


d1 = Parent()
d2 = DeepParent()
print(str(d1))
print(str(d2))
```