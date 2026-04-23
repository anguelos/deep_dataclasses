from __future__ import annotations
import pytest
import dataclasses
from deep_dataclasses import deep_dataclass
# Compatibillity with PEP 563: Postpone evaluation of annotations, so that string 
# annotations are supported without needing to import from __future__ in the test 
# code.  This is important for testing that string annotations work correctly in 
# nested classes, which is a common use case for deep_dataclass.


@deep_dataclass
class Config:
    class Model:
        layers: int = 3
    lr: float = 0.01


def test_future_annotations_default():
    assert Config() == Config(Model=Config.Model(), lr=0.01)


def test_future_annotations_roundtrip():
    c = Config()
    assert Config(**dataclasses.asdict(c)) == c


def test_future_annotations_coerce():
    c = Config(Model={"layers": 5})
    assert isinstance(c.Model, Config.Model)
    assert c.Model.layers == 5

def test_future_annotations_local_definition():
    @deep_dataclass
    class LocalConfig:
        class LocalModel:
            layers: int = 3
        lr: float = 0.01
    assert LocalConfig() == LocalConfig(LocalModel=LocalConfig.LocalModel(), lr=0.01)