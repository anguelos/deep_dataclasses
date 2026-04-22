import pytest
import dataclasses
from deep_dataclasses import deep_dataclass


def are_equivalent_dataclasses(dc1, dc2):
    if type(dc1) != type(dc2):
        return False
    if dataclasses.is_dataclass(dc1):
        for field in dataclasses.fields(dc1):
            if not are_equivalent_dataclasses(getattr(dc1, field.name), getattr(dc2, field.name)):
                return False
        return True
    return dc1 == dc2


def test_nested_unested_dataclass_equivalence():
    @deep_dataclass
    class Inner:
        x: int
        y: int

    @deep_dataclass
    class Outer:
        a: int
        b: Inner

    inner1 = Inner(1, 2)
    inner2 = Inner(1, 2)
    outer1 = Outer(3, inner1)
    outer2 = Outer(3, inner2)

    assert are_equivalent_dataclasses(outer1, outer2)