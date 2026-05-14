from __future__ import annotations

from typing import Optional

import pytest
from dataclass_wizard import asdict, fromdict

from deep_dataclasses import deep_dataclass


@deep_dataclass(autosnake=True)
class Root:
    class Training:
        class Optimizer:
            lr: float = 1e-3

        epochs: int = 10
        tag: Optional[str] = None

    seed: int = 42


def test_simple_correct_values():
    # correct — fromdict reconstructs full hierarchy
    r = fromdict(Root, {'training': {'optimizer': {'lr': 0.05}, 'epochs': 5, 'tag': 'v1'}, 'seed': 7})
    assert r.seed == 7 and r.training.optimizer.lr == 0.05 and r.training.tag == 'v1'

    # round-trip via asdict
    assert fromdict(Root, asdict(r)) == r


def test_wrong_types():
    # bad type — list can't be coerced to float
    with pytest.raises(TypeError):
        fromdict(Root, {'training': {'optimizer': {'lr': [1, 2, 3]}}})


def test_optional_fields():
    # missing optional field — fromdict allows it and sets it to None
    r1 = fromdict(Root, {'training': {'optimizer': {}}})
    assert r1.training.tag is None

    r2 = fromdict(Root, {'training': {'optimizer': {}, 'tag': None}})
    assert r2.training.tag is None
