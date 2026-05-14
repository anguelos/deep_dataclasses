import dataclasses
from dataclasses import field
from typing import List

import pytest

from deep_dataclasses import deep_dataclass, auxiliary


class TestChildInheritsParentFields:
    def test_parent_inner_class_field_present(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            pass

        assert 'Config' in {f.name for f in dataclasses.fields(Child)}

    def test_parent_inner_class_instantiates(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            pass

        c = Child()
        assert isinstance(c.Config, Parent.Config)
        assert c.Config.lr == 1e-3

    def test_parent_annotated_fields_inherited(self):
        @deep_dataclass
        class Parent:
            x: int = 0
            y: int = 1

        @deep_dataclass
        class Child(Parent):
            pass

        c = Child()
        assert c.x == 0
        assert c.y == 1


class TestChildOwnFields:
    def test_child_own_inner_class_promoted(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            class Scheduler:
                step: int = 10

        field_names = {f.name for f in dataclasses.fields(Child)}
        assert 'Config' in field_names
        assert 'Scheduler' in field_names

    def test_child_own_inner_class_instantiates(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            class Scheduler:
                step: int = 10

        c = Child()
        assert isinstance(c.Scheduler, Child.Scheduler)
        assert c.Scheduler.step == 10

    def test_child_annotated_field_with_default(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            name: str = "hello"

        field_names = {f.name for f in dataclasses.fields(Child)}
        assert 'Config' in field_names
        assert 'name' in field_names
        assert Child().name == "hello"

    def test_child_fields_not_silently_dropped(self):
        """Regression: before the is_dataclass fix, a child's mandatory field was
        silently dropped because is_dataclass(Child) returned True via MRO inheritance
        of __dataclass_fields__, causing _apply to skip @dataclass on the child."""
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        with pytest.raises(TypeError):
            @deep_dataclass
            class Child(Parent):
                model_path: str  # mandatory — must not be silently ignored

    def test_child_own_dataclass_fields_set(self):
        """After decoration, __dataclass_fields__ must be in the child's own __dict__,
        not just inherited — confirming @dataclass was actually applied to the child."""
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            name: str = "hello"

        assert '__dataclass_fields__' in vars(Child)


class TestInheritanceTypeError:
    def test_mandatory_field_after_parent_defaults_raises(self):
        @deep_dataclass
        class Parent:
            fond: List[str] = field(default_factory=list)
            charter: List[str] = field(default_factory=list)

        with pytest.raises(TypeError):
            @deep_dataclass
            class Child(Parent):
                model_path: str

    def test_error_names_the_mandatory_field(self):
        @deep_dataclass
        class Parent:
            x: int = 0

        with pytest.raises(TypeError, match="model_path"):
            @deep_dataclass
            class Child(Parent):
                model_path: str

    def test_error_names_the_parent_class(self):
        @deep_dataclass
        class SomeParent:
            x: int = 0

        with pytest.raises(TypeError, match="SomeParent"):
            @deep_dataclass
            class Child(SomeParent):
                model_path: str

    def test_all_defaulted_child_fields_do_not_raise(self):
        @deep_dataclass
        class Parent:
            class Config:
                lr: float = 1e-3

        @deep_dataclass
        class Child(Parent):
            name: str = "hello"

        assert Child().name == "hello"

    def test_exact_user_reported_case(self):
        """Exact case from the bug report: List fields in parent, mandatory str in child."""
        @deep_dataclass
        class CharterFargv:
            fond: List[str] = field(default_factory=lambda: [])
            charter: List[str] = field(default_factory=lambda: [])
            archive: List[str] = field(default_factory=lambda: [])

        with pytest.raises(TypeError):
            @deep_dataclass
            class MyConfig(CharterFargv):
                model_path: str


class TestAuxiliaryInheritanceNotContagious:
    """Subclasses of @auxiliary inner classes must still become fields."""

    def test_subclass_of_auxiliary_is_promoted_to_field(self):
        @deep_dataclass
        class Outer:
            @auxiliary
            class Base:
                x: int = 0

            class Concrete(Base):
                y: int = 1

        field_names = {f.name for f in dataclasses.fields(Outer)}
        assert 'Concrete' in field_names
        assert 'Base' not in field_names

    def test_subclass_of_auxiliary_default_constructs(self):
        @deep_dataclass
        class Outer:
            @auxiliary
            class Base:
                x: int = 0

            class Concrete(Base):
                y: int = 1

        o = Outer()
        assert isinstance(o.Concrete, Outer.Concrete)
        assert o.Concrete.x == 0
        assert o.Concrete.y == 1

    def test_multiple_subclasses_of_auxiliary_all_promoted(self):
        @deep_dataclass
        class Outer:
            @auxiliary
            class Base:
                host: str = 'localhost'

            class ServiceA(Base):
                port: int = 8000

            class ServiceB(Base):
                port: int = 9000

        field_names = {f.name for f in dataclasses.fields(Outer)}
        assert field_names == {'ServiceA', 'ServiceB'}
