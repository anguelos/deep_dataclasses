import sys

sys.path.insert(0, '/tmp')

import dataclasses
from dataclasses import field
from typing import List

import pytest
from deep_dataclasses import deep_dataclass



class TestEmptyCollectionsAutoWrapped:
    def test_empty_list(self):
        @deep_dataclass
        class A:
            items: list = []

        assert A().items == []

    def test_empty_dict(self):
        @deep_dataclass
        class A:
            meta: dict = {}

        assert A().meta == {}

    def test_empty_set(self):
        @deep_dataclass
        class A:
            ids: set = set()

        assert A().ids == set()

    def test_empty_list_not_shared(self):
        @deep_dataclass
        class A:
            items: list = []

        assert A().items is not A().items

    def test_empty_dict_not_shared(self):
        @deep_dataclass
        class A:
            meta: dict = {}

        assert A().meta is not A().meta

    def test_empty_set_not_shared(self):
        @deep_dataclass
        class A:
            ids: set = set()

        assert A().ids is not A().ids

    def test_empty_list_factory_is_list_type(self):
        @deep_dataclass
        class A:
            items: list = []

        f = dataclasses.fields(A)[0]
        assert f.default_factory is list

    def test_empty_dict_factory_is_dict_type(self):
        @deep_dataclass
        class A:
            meta: dict = {}

        f = dataclasses.fields(A)[0]
        assert f.default_factory is dict

    def test_empty_set_factory_is_set_type(self):
        @deep_dataclass
        class A:
            ids: set = set()

        f = dataclasses.fields(A)[0]
        assert f.default_factory is set


class TestNonEmptyPrimitiveCollections:
    def test_list_of_ints(self):
        @deep_dataclass
        class A:
            scores: list = [1, 2, 3]

        assert A().scores == [1, 2, 3]

    def test_list_of_strs(self):
        @deep_dataclass
        class A:
            tags: list = ['a', 'b']

        assert A().tags == ['a', 'b']

    def test_list_of_floats(self):
        @deep_dataclass
        class A:
            vals: list = [1.0, 2.5]

        assert A().vals == [1.0, 2.5]

    def test_list_of_bools(self):
        @deep_dataclass
        class A:
            flags: list = [True, False]

        assert A().flags == [True, False]

    def test_list_with_none(self):
        @deep_dataclass
        class A:
            items: list = [1, None, 'x']

        assert A().items == [1, None, 'x']

    def test_non_empty_list_not_shared(self):
        @deep_dataclass
        class A:
            scores: list = [1, 2, 3]

        assert A().scores is not A().scores

    def test_dict_with_primitive_values(self):
        @deep_dataclass
        class A:
            config: dict = {'lr': 0.01, 'epochs': 10}

        assert A().config == {'lr': 0.01, 'epochs': 10}

    def test_non_empty_dict_not_shared(self):
        @deep_dataclass
        class A:
            config: dict = {'lr': 0.01}

        assert A().config is not A().config

    def test_set_of_ints(self):
        @deep_dataclass
        class A:
            ids: set = {1, 2, 3}

        assert A().ids == {1, 2, 3}

    def test_non_empty_set_not_shared(self):
        @deep_dataclass
        class A:
            ids: set = {1, 2}

        assert A().ids is not A().ids

    def test_mixed_primitive_types_in_list(self):
        @deep_dataclass
        class A:
            items: list = [1, 'x', 3.14, True, None]

        assert A().items == [1, 'x', 3.14, True, None]


class TestNonPrimitiveElementsRejected:
    def test_list_with_object_instance(self):
        with pytest.raises(TypeError, match='non-primitive'):

            @deep_dataclass
            class A:
                items: list = [object()]

    def test_list_with_external_class_instance(self):
        class Point:
            pass

        with pytest.raises(TypeError, match='non-primitive'):

            @deep_dataclass
            class A:
                items: list = [Point()]

    def test_dict_with_non_primitive_value(self):
        with pytest.raises(TypeError, match='non-primitive'):

            @deep_dataclass
            class A:
                meta: dict = {'key': object()}

    def test_dict_with_non_primitive_key(self):
        with pytest.raises(TypeError):

            @deep_dataclass
            class A:
                meta: dict = {object(): 'value'}

    def test_set_with_non_primitive(self):
        bad = set()
        bad.add(object())
        with pytest.raises(TypeError, match='non-primitive'):

            @deep_dataclass
            class A:
                ids: set = bad

    def test_error_message_names_field(self):
        with pytest.raises(TypeError, match='my_field'):

            @deep_dataclass
            class A:
                my_field: list = [object()]


class TestExplicitFieldNotRewrapped:
    def test_explicit_field_default_factory_untouched(self):
        sentinel = []

        @deep_dataclass
        class A:
            items: list = field(default_factory=lambda: sentinel)

        assert A().items is sentinel

    def test_explicit_field_with_list_default_factory(self):
        @deep_dataclass
        class A:
            items: List[int] = field(default_factory=list)

        f = dataclasses.fields(A)[0]
        assert f.default_factory is list


class TestImmutableCollectionsUnchanged:
    def test_tuple_default_unchanged(self):
        @deep_dataclass
        class A:
            coords: tuple = (1, 2, 3)

        assert A().coords == (1, 2, 3)

    def test_frozenset_default_unchanged(self):
        @deep_dataclass
        class A:
            ids: frozenset = frozenset([1, 2, 3])

        assert A().ids == frozenset([1, 2, 3])


class TestSetAndFrozensetCoercion:
    def test_set_field_coerced_from_list(self):
        from typing import Set

        @deep_dataclass
        class A:
            ids: Set[int] = field(default_factory=set)

        a = A(ids=[1, 2, 3])
        assert isinstance(a.ids, set)
        assert a.ids == {1, 2, 3}

    def test_frozenset_field_coerced_from_list(self):
        from typing import FrozenSet

        @deep_dataclass
        class A:
            ids: FrozenSet[int] = field(default_factory=frozenset)

        a = A(ids=[1, 2, 3])
        assert isinstance(a.ids, frozenset)
        assert a.ids == frozenset({1, 2, 3})

    def test_frozenset_field_coerced_from_set(self):
        from typing import FrozenSet

        @deep_dataclass
        class A:
            ids: FrozenSet[int] = field(default_factory=frozenset)

        a = A(ids={4, 5})
        assert isinstance(a.ids, frozenset)
        assert a.ids == frozenset({4, 5})

    def test_set_field_roundtrip(self):
        from dataclasses import asdict
        from typing import Set

        @deep_dataclass
        class A:
            ids: Set[int] = field(default_factory=set)

        a = A(ids={1, 2})
        assert A(**asdict(a)).ids == a.ids
