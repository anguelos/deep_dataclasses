from __future__ import annotations
from typing import Optional, Union
enable_future_annotations = True


import pytest
import dataclasses
from dataclasses import dataclass, field, asdict
from deep_dataclasses import deep_dataclass, auxiliary, to_json_schema
import jsonschema


def test_simple_dataclass():
    @dataclass
    class Config:
        lr: float = 1e-3
        beta1: float = 0.9
        momentum: float = 0.9
        device: str = "cpu"
        seed: Optional[int] = 42

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "lr" in schema["properties"]
    assert "beta1" in schema["properties"]
    assert "momentum" in schema["properties"]
    assert "device" in schema["properties"]
    assert "seed" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"lr": 0.01, "beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"lr": "not_a_float", "beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)
    
    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({"lr": 0.01, "beta1": 0.8, "momentum": 0.95, "device": "cuda"}, config_schema)


def test_simple_deep_dataclass():
    @deep_dataclass
    class Config:
        lr: float = 1e-3
        beta1: float = 0.9
        momentum: float = 0.9
        device: str = "cpu"
        seed: Optional[int] = 42

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "lr" in schema["properties"]
    assert "beta1" in schema["properties"]
    assert "momentum" in schema["properties"]
    assert "device" in schema["properties"]
    assert "seed" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"lr": 0.01, "beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"lr": "not_a_float", "beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)
    
    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"beta1": 0.8, "momentum": 0.95, "device": "cuda", "seed": 123}, config_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({"lr": 0.01, "beta1": 0.8, "momentum": 0.95, "device": "cuda"}, config_schema)


def test_nested_dataclass():
    @dataclass
    class Config:
        @dataclass
        class Train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        train: Train = field(default_factory=Train)
        seed: int = 42

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "train" in schema["properties"]
    assert "seed" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"train": {"lr": 0.01, "pseudo_batch_size": 32}, "seed": 123}, config_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"lr": "not_a_float", "pseudo_batch_size": 32}, "seed": 123}, config_schema)
    
    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"pseudo_batch_size": 32}, "seed": 123}, config_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({"train": {"lr": 0.01}, "seed": 123}, config_schema)


def test_deep_dataclass():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        seed: int = 42

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "train" in schema["properties"]
    assert "seed" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"train": {"lr": 0.01, "pseudo_batch_size": 32}, "seed": 123}, config_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"lr": "not_a_float", "pseudo_batch_size": 32}, "seed": 123}, config_schema)
    
    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"pseudo_batch_size": 32}, "seed": 123}, config_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({"train": {"lr": 0.01}, "seed": 123}, config_schema)


def test_deep_dataclass_nested_dataclass_equivalence():
    @deep_dataclass(autosnake=True)
    class DeepConfig:
        class Train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        seed: int = 42

    @dataclass
    class NestedConfig:
        @dataclass
        class Train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        train: Train = field(default_factory=Train)
        seed: int = 42

    assert to_json_schema(DeepConfig) == to_json_schema(NestedConfig)


def test_unions():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        seed: int = 42
        id: Union[int, str] = "id123"

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "train" in schema["properties"]
    assert "seed" in schema["properties"]
    assert "id" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"train": {"lr": 0.01, "pseudo_batch_size": 32}, "seed": 123, "id": "id4711"}, config_schema)

    # wrong type in Union — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"lr": "0.001", "pseudo_batch_size": 32}, "seed": 123, "id": 123.456}, config_schema)
    
    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"train": {"pseudo_batch_size": 32}, "seed": 123, "id": "id4711"}, config_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({"train": {"lr": 0.01}, "seed": 123, "id": "id4711"}, config_schema)