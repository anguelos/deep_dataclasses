from __future__ import annotations
import pytest
from typing import Optional, Union, List, Dict, Tuple
from dataclasses import dataclass, field, asdict
from deep_dataclasses import deep_dataclass, auxiliary


def test_nested_optional_field():
    @deep_dataclass
    class Outer:
        class Inner:
            @auxiliary
            class Sub:
                x: int = 0
            opt_sub: Optional[Sub] = None
        inner: Inner

    assert Outer(inner={"opt_sub": {"x": 5}}).inner.opt_sub.x == 5
    assert Outer(inner={"opt_sub": None}).inner.opt_sub is None
    assert Outer(**asdict(Outer(inner={"opt_sub": {"x": 7}}))).inner.opt_sub.x == 7


def test_nested_union_field():
    @deep_dataclass(autosnake=True)
    class Outer:
        class Inner:
            @auxiliary
            class SubA:
                a: str = ""
            @auxiliary
            class SubB:
                b: int = 0
            sub: Union[SubA, SubB] = field(default_factory=SubA)
    #    inner: Inner 

    o = Outer(inner={"sub": {"a": "hello"}})
    assert isinstance(o.inner.sub, Outer.Inner.SubA)
    assert o.inner.sub.a == "hello"

    o = Outer(inner={"sub": {"b": 42}})
    assert isinstance(o.inner.sub, Outer.Inner.SubB)
    assert o.inner.sub.b == 42


def test_nested_dict_fields():
    @deep_dataclass(autosnake=True)
    class Outer:
        class Inner:
            @auxiliary
            class Sub:
                x: int = 0
            items: Dict[str, Sub] = field(default_factory=dict)
            raw: dict = field(default_factory=dict)
    #    inner: Inner

    o = Outer(inner={"items": {"k": {"x": 7}}, "raw": {"foo": "bar"}})
    assert o.inner.items["k"].x == 7
    assert o.inner.raw == {"foo": "bar"}
    assert Outer(**asdict(o)) == o


def test_nested_list_and_tuple_fields():
    @deep_dataclass(autosnake=True)
    class Outer:
        class Inner:
            @auxiliary
            class Sub:
                x: int = 0
            sub_list: List[Sub] = field(default_factory=list)
            coords: Tuple[int, int] = (0, 0)
            tags: List[str] = field(default_factory=list)
    #    inner: Inner

    o = Outer(inner={
        "sub_list": [{"x": 1}, {"x": 2}],
        "coords": (3, 4),
        "tags": ["a", "b"],
    })
    assert o.inner.sub_list[0].x == 1
    assert o.inner.sub_list[1].x == 2
    assert o.inner.coords == (3, 4)
    assert o.inner.tags == ["a", "b"]