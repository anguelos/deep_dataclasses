from __future__ import annotations

enable_future_annotations = True


from dataclasses import asdict, dataclass, field

from deep_dataclasses import deep_dataclass


# The class definition setup is defined outside the test function to ensure that the same class objects are used in both cases, so that any differences in behavior are due to the dataclass transformation and not due to different class objects.
@dataclass
class GrandChild:
    grandchild_str: str = 'grandchild1'
    grandchild_num: int = 1


@dataclass
class Child:
    grandchild: GrandChild = field(default_factory=GrandChild)
    child_str: str = 'child'


@dataclass
class Parent:
    child: Child = field(default_factory=Child)
    parent_str: str = 'parent'


@deep_dataclass
class DeepParent:
    class child:
        class grandchild:
            grandchild_str: str = 'grandchild1'
            grandchild_num: int = 1

        child_str: str = 'child'

    parent_str: str = 'parent'


def test_multiple_children():
    # Test that multiple children are correctly transformed and that their fields are accessible.
    @deep_dataclass
    class Parent1:
        class child1:
            class grandchild1:
                grandchild_str: str = 'ch1_grandchild1'
                grandchild_num: int = 1

            class grandchild2:
                grandchild_str: str = 'ch1_grandchild2'
                grandchild_num: int = 2

            child1_str: str = 'child1'

        class child2:
            class grandchild1:
                grandchild_str: str = 'ch2_grandchild1'
                grandchild_num: int = 1

            class grandchild2:
                grandchild_str: str = 'ch2_grandchild2'
                grandchild_num: int = 2

            child2_str: str = 'child2'

        parent_str: str = 'parent'

    assert Parent1().child1.grandchild1.grandchild_str == 'ch1_grandchild1'
    assert Parent1().child1.grandchild2.grandchild_str == 'ch1_grandchild2'
    assert Parent1().child1.child1_str == 'child1'
    assert Parent1().child2.grandchild1.grandchild_str == 'ch2_grandchild1'
    assert Parent1().child2.grandchild2.grandchild_str == 'ch2_grandchild2'
    assert Parent1().child2.child2_str == 'child2'
    assert Parent1().parent_str == 'parent'
    assert asdict(Parent1()) == {
        'child1': {
            'grandchild1': {'grandchild_str': 'ch1_grandchild1', 'grandchild_num': 1},
            'grandchild2': {'grandchild_str': 'ch1_grandchild2', 'grandchild_num': 2},
            'child1_str': 'child1',
        },
        'child2': {
            'grandchild1': {'grandchild_str': 'ch2_grandchild1', 'grandchild_num': 1},
            'grandchild2': {'grandchild_str': 'ch2_grandchild2', 'grandchild_num': 2},
            'child2_str': 'child2',
        },
        'parent_str': 'parent',
    }
    assert Parent1(**asdict(Parent1())) == Parent1()


def test_nested_unnested_dataclass_equivalence():
    assert asdict(Parent()) == asdict(DeepParent())


def test_asdict_neutrality():
    # asdict should produce the same output for both dataclasses, and should not modify the original objects.
    assert DeepParent() == DeepParent(**asdict(Parent()))
    assert DeepParent() == DeepParent(**asdict(Parent()))


def test_repr():
    # asdict should produce the same output for both dataclasses, and should not modify the original objects.
    # repr should be serialising correctly both dataclasses, and eval(repr(...)) should produce an equivalent object.
    assert eval(repr(Parent())) == Parent()
    assert eval(repr(DeepParent())) == DeepParent()

    assert asdict(DeepParent(**asdict(DeepParent()))) == asdict(eval(repr(Parent())))


def test_partial_dict_coercion():
    # Test that dict coercion works at all levels of the hierarchy.
    dp = DeepParent(child={'grandchild': {'grandchild_str': 'gc2', 'grandchild_num': 2}, 'child_str': 'c2'}, parent_str='p2')
    assert dp.parent_str == 'p2'
    assert dp.child.child_str == 'c2'
    assert dp.child.grandchild.grandchild_str == 'gc2'
    assert dp.child.grandchild.grandchild_num == 2

    # Supress an entry in the grandchild dict to test that defaults are preserved.
    dp = DeepParent(child={'grandchild': {'grandchild_num': 2}, 'child_str': 'c2'}, parent_str='p2')
    assert dp.parent_str == 'p2'
    assert dp.child.child_str == 'c2'
    assert dp.child.grandchild.grandchild_str == 'grandchild1'
    assert dp.child.grandchild.grandchild_num == 2

    # Supress an entry in granchild and child dict to test that defaults are preserved.
    dp = DeepParent(child={'grandchild': {'grandchild_num': 2}}, parent_str='p2')
    assert dp.parent_str == 'p2'
    assert dp.child.child_str == 'child'
    assert dp.child.grandchild.grandchild_str == 'grandchild1'
    assert dp.child.grandchild.grandchild_num == 2

    # Supress an entry in child dict to test that defaults are preserved.
    dp = DeepParent(child={'grandchild': {'grandchild_str': 'gc2', 'grandchild_num': 2}}, parent_str='p2')
    assert dp.parent_str == 'p2'
    assert dp.child.child_str == 'child'
    assert dp.child.grandchild.grandchild_str == 'gc2'
    assert dp.child.grandchild.grandchild_num == 2

    # Supress the whole child entry dict to test that defaults are preserved.
    dp = DeepParent(parent_str='p2')
    assert dp.parent_str == 'p2'
    assert dp.child.child_str == 'child'
    assert dp.child.grandchild.grandchild_str == 'grandchild1'
    assert dp.child.grandchild.grandchild_num == 1


def test_type_as_value():
    # Test that we can construct a DeepParent with a mix of dicts and dataclass instances.
    @deep_dataclass
    class Parent1:
        class child:
            child_str: str = 'child'
            child_type: type = list

        parent_str: str = 'parent'

    assert type([]) == Parent1().child.child_type


def test_hybrid_construction():
    # Test that we can construct a DeepParent with a mix of dicts and dataclass instances.
    @deep_dataclass
    class HybridParent1:
        class child:
            grandchild: GrandChild = field(default_factory=GrandChild)
            child_str: str = 'child'

        parent_str: str = 'parent'

    assert asdict(HybridParent1()) == asdict(Parent()) == asdict(DeepParent())


def test_redecoration():
    if enable_future_annotations:
        # future annotations dont work with local classes, so we can't test redecorating
        # the same class with both dataclass and deep_dataclass, but we can test that
        # redecorating with the same decorator is a no-op.
        return

    assert not Parent(**asdict(Parent())) == Parent()

    @dataclass
    class GrandChild1:
        grandchild_str: str = 'grandchild1'
        grandchild_num: int = 1

    @dataclass
    class Child1:
        grandchild: GrandChild1 = field(default_factory=GrandChild1)
        child_str: str = 'child'

    @deep_dataclass
    @dataclass
    class Parent1:
        child: Child1 = field(default_factory=Child1)
        parent_str: str = 'parent'

    # Test that applying deep_dataclass to an already decorated dataclass will make it coerse dicts.
    assert Parent1(**asdict(Parent1())) == Parent1()

    # Test that applying dataclass to an already decorated deep_dataclass is a no-op.
    @dataclass
    @deep_dataclass
    class Parent2:
        class child:
            class grandchild:
                grandchild_str: str = 'grandchild1'
                grandchild_num: int = 1

            child_str: str = 'child'

        parent_str: str = 'parent'

    assert asdict(Parent2()) == asdict(Parent1()) == asdict(DeepParent())

    @deep_dataclass
    @deep_dataclass
    class Parent3:
        class child:
            class grandchild:
                grandchild_str: str = 'grandchild1'
                grandchild_num: int = 1

            child_str: str = 'child'

        parent_str: str = 'parent'

    assert asdict(Parent3()) == asdict(Parent1()) == asdict(DeepParent())
    assert Parent3(**asdict(Parent3())) == Parent3()


def test_methods_and_properties_preserved():
    # Test that methods and properties defined on the original class are preserved after decoration.
    @deep_dataclass
    class Parent1:
        class child:
            class grandchild:
                grandchild_str: str = 'grandchild1'
                grandchild_num: int = 1

            child_str: str = 'child'

        parent_str: str = 'parent'

        def method(self):
            return 'method result'

        @property
        def prop(self):
            return 'property result'

    p1 = Parent1()
    assert p1.method() == 'method result'
    assert p1.prop == 'property result'


def test_field_specifications_preserved():
    # Test that field specifications defined on the original class are preserved after decoration.
    @deep_dataclass
    class Parent1:
        class child:
            class grandchild:
                grandchild_str: str = 'grandchild1'
                grandchild_num: int = 1

            child_str: str = 'child'

        parent_str: str = 'parent'

        field_with_default: int = 42
        field_with_factory: list = field(default_factory=list)
        field_with_metadata: str = field(default='default', metadata={'meta': 'data'})

    p1 = Parent1()
    assert p1.field_with_default == 42
    assert p1.field_with_factory == []
    assert p1.field_with_metadata == 'default'
    assert Parent1.__dataclass_fields__['field_with_metadata'].metadata == {'meta': 'data'}


def test_order_preserved_in_hidden():
    # Test that the order of fields is preserved in the __dataclass_fields__ attribute, even for fields that are not
    # defined in the original class but are added by deep_dataclass (e.g. for inline inner classes).
    @deep_dataclass
    class Parent1:
        _first_hidden: int = 1
        shown: int = 2
        _second_hidden: int = 3
        shown2: int = 4
        _third_hidden: int = 5

    field_names = list(Parent1.__dataclass_fields__.keys())
    assert field_names == ['_first_hidden', 'shown', '_second_hidden', 'shown2', '_third_hidden']


def test_autosnake():
    # Test that autosnake converts PascalCase inner class names to snake_case field names, while preserving the original class attributes.
    @deep_dataclass(autosnake=True)
    class Parent1:
        class ChildSolver:
            lr: float = 1e-3
            momentum: float = 0.9

        parent_str: str = 'parent'

    assert hasattr(Parent1, 'ChildSolver')
    assert Parent1.ChildSolver.lr == 1e-3
    assert Parent1.ChildSolver.momentum == 0.9
    assert hasattr(Parent1, 'child_solver')
    assert Parent1.child_solver.lr == 1e-3
    assert Parent1.child_solver.momentum == 0.9

    # assert eval(repr(Parent1())) == Parent1()
    assert Parent1(**asdict(Parent1())) == Parent1()
