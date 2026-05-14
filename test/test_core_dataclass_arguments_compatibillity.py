from __future__ import annotations

import dataclasses

import pytest

from deep_dataclasses import deep_dataclass


def test_frozen():
    @deep_dataclass(frozen=True)
    class C:
        x: int = 0

    with pytest.raises(dataclasses.FrozenInstanceError):
        C().x = 1


def test_frozen_roundtrip():
    @deep_dataclass(frozen=True)
    class C:
        class Inner:
            y: float = 1.0

        x: int = 0

    c = C()
    assert C(**dataclasses.asdict(c)) == c


def test_eq_false():
    @deep_dataclass(eq=False)
    class C:
        x: int = 0

    assert C() != C()  # identity, not value


def test_order():
    @deep_dataclass(order=True)
    class C:
        x: int = 0

    assert C(x=1) > C(x=0)


def test_init_false_raises():
    with pytest.raises(TypeError):

        @deep_dataclass(init=False)
        class C:
            x: int = 0


def test_unsafe_hash():
    @deep_dataclass(unsafe_hash=True)
    class C:
        x: int = 0

    assert hash(C(x=1)) == hash(C(x=1))


def test_custom_post_init():
    @deep_dataclass
    class Config:
        class Inner:
            x: int = 0

        counter: int = 0

        def __post_init__(self):
            self.counter += 1

    c = Config(Inner={'x': 5})
    assert c.Inner.x == 5
    assert c.counter == 1
