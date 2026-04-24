from __future__ import annotations
from typing import Optional, Union
enable_future_annotations = True


import pytest
import dataclasses
from dataclasses import dataclass, field, asdict
from deep_dataclasses import deep_dataclass, auxiliary, to_json_schema
import jsonschema


def test_class_unions():
    @deep_dataclass
    class Config:
        @auxiliary
        class Train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        @auxiliary
        class Test:
            metric: str = "accuracy"
        @auxiliary
        class ViewParameters:
            resolution: str = "1080p"
            fontsize: int = 18
        seed: int = 42
        mode: Union[Train, Test] = field(default_factory=Train)
        view_parameters: Optional[ViewParameters] = None

    schema = to_json_schema(Config)
    assert schema["type"] == "object"
    assert "mode" in schema["properties"]

    config_schema = to_json_schema(Config)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({"mode": {"lr": 0.01, "pseudo_batch_size": 32}, "seed": 123}, config_schema)

    # wrong type in Union — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"mode": {"lr": "0.001", "pseudo_batch_size": 32}, "seed": 123}, config_schema)
    
    # invalid union assignment — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"mode": {"resolution": "720p", "fontsize": 18}, "seed": 123}, config_schema)

    # alternative must also be valid
    jsonschema.validate({"mode": {"metric": "f1"}, "seed": 123}, config_schema)
    


def test_optional_unions():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32
        seed: int = 42
        id: Optional[Union[int, str]] = "id123"

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