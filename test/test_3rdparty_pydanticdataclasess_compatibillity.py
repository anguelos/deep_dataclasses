from __future__ import annotations

import dataclasses
from typing import Optional

import pytest
from pydantic import TypeAdapter, ValidationError

from deep_dataclasses import deep_dataclass


@deep_dataclass(autosnake=True)
class Root:
    class Training:
        class Optimizer:
            lr: float = 1e-3

        epochs: int = 10
        tag: Optional[str] = None

    seed: int = 42


def test_pydantic_compatibility():
    # Verify that pydantic's TypeAdapter can validate and coerce dicts into the deep dataclass hierarchy, including nested classes and optional fields.
    ta = TypeAdapter(Root)

    # correct
    r = ta.validate_python({'training': {'optimizer': {'lr': 0.05}, 'epochs': 5, 'tag': 'v1'}, 'seed': 7})
    assert r.seed == 7 and r.training.optimizer.lr == 0.05 and r.training.tag == 'v1'

    # round-trip
    assert ta.validate_python(dataclasses.asdict(r)) == r

    # coercion — pydantic converts "5" -> 5 for int fields
    r2 = ta.validate_python({'training': {'optimizer': {}, 'epochs': '5'}, 'seed': 42})
    assert r2.training.epochs == 5


def test_pydantic_rejects_wrong_types():
    # wrong type — pydantic raises ValidationError
    ta = TypeAdapter(Root)
    with pytest.raises(ValidationError):
        ta.validate_python({'training': {'optimizer': {'lr': 'not_a_float'}}})


def test_pydantic_allows_optional_fields():
    # missing optional field — pydantic allows it and sets it to None
    ta = TypeAdapter(Root)
    r1 = ta.validate_python({'training': {'optimizer': {}}})
    assert r1.training.tag is None

    r2 = ta.validate_python({'training': {'optimizer': {}, 'tag': None}})
    assert r2.training.tag is None
