```python
import dataclass, deep_dataclass


@dataclass
class GrandChild:
    grandchild_str: str = "grandchild1"
    grandchild_num: int = 1


@dataclass
class Child:
    child_str: str = "child"
    grandchild: Grandchild


@dataclass
class Parent:
    parent_str: str = "parent"
    child: Child


@deep_dataclass
class DeepParent:
    parent_str: str = "parent"
    class Child:
        child_str: str = "child"
        class GrandChild:
            grandchild_str: str = "grandchild1"
            grandchild_num: int = 1
```