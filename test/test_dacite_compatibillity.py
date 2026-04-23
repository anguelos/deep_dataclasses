import pytest
import dataclasses
from typing import Optional
from dacite import from_dict, Config as DaciteConfig, WrongTypeError
from deep_dataclasses import deep_dataclass


@deep_dataclass
class Root:
    class Training:
        class Optimizer:
            lr: float = 1e-3
        epochs: int = 10
        tag: Optional[str] = None
    seed: int = 42


@deep_dataclass(autosnake=True)
class RootSnake:
    class Training:
        class Optimizer:
            lr: float = 1e-3
        epochs: int = 10
        tag: Optional[str] = None
    seed: int = 42


def test_simple_dict_coercion():
    # correct — dacite reconstructs full hierarchy
    r = from_dict(Root, {"Training": {"Optimizer": {"lr": 0.05}, "epochs": 5, "tag": "v1"}, "seed": 7})
    assert r.seed == 7 and r.Training.Optimizer.lr == 0.05 and r.Training.tag == "v1"

    r2 = from_dict(RootSnake, {"training": {"optimizer": {"lr": 0.05}, "epochs": 5, "tag": "v1"}, "seed": 7})
    assert r2.seed == 7 and r2.training.optimizer.lr == 0.05 and r2.training.tag == "v1"


def test_dacite_rejects_wrong_types():
    # wrong type — strict mode catches it
    with pytest.raises(WrongTypeError):
        from_dict(Root, {"Training": {"Optimizer": {"lr": "oops"}, "epochs": 5}, "seed": 42},
                config=DaciteConfig(strict=True))
    
    with pytest.raises(WrongTypeError):
        from_dict(RootSnake, {"training": {"optimizer": {"lr": "oops"}, "epochs": 5}, "seed": 42},
                config=DaciteConfig(strict=True))


def test_dacite_allows_optional_fields():
    # missing optional field — dacite allows it and sets it to None
    r1 = from_dict(Root, {"Training": {"Optimizer": {}}})
    assert r1.Training.tag is None

    r2 = from_dict(Root, {"Training": {"Optimizer": {}, "tag": None}})
    assert r2.Training.tag is None