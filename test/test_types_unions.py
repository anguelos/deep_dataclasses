from __future__ import annotations

import sys
from dataclasses import field
from typing import Optional, Union

import jsonschema
import pytest

from deep_dataclasses import auxiliary, deep_dataclass, to_json_schema


def test_class_unions():
    @deep_dataclass
    class Config:
        @auxiliary
        class Train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32

        @auxiliary
        class Test:
            metric: str = 'accuracy'
            cross_validation_folds: int = 5
            report_style: str = 'detailed'

        @auxiliary
        class ViewParameters:
            resolution: str = '1080p'
            fontsize: int = 18

        seed: int = 42
        mode: Union[Train, Test] = field(default_factory=Train)
        view_parameters: Optional[ViewParameters] = None

    schema = to_json_schema(Config)
    assert schema['type'] == 'object'
    assert 'mode' in schema['properties']

    strict_schema = to_json_schema(Config, strict=False)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'mode': {'lr': 0.01, 'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # invalid union assignment — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'mode': {'resolution': '720p', 'fontsize': 18}, 'seed': 123}, strict_schema)

    # alternative must also be valid
    jsonschema.validate({'mode': {'metric': 'f1'}, 'seed': 123}, strict_schema)


def test_optional_unions():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32

        seed: int = 42
        id: Optional[Union[int, str]] = 'id123'

    schema = to_json_schema(Config)
    assert schema['type'] == 'object'
    assert 'train' in schema['properties']
    assert 'seed' in schema['properties']
    assert 'id' in schema['properties']

    strict_schema = to_json_schema(Config, strict=True)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'train': {'lr': 0.01, 'pseudo_batch_size': 32}, 'seed': 123, 'id': 'id4711'}, strict_schema)

    # wrong type in Union — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'lr': '0.001', 'pseudo_batch_size': 32}, 'seed': 123, 'id': 123.456}, strict_schema)

    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'pseudo_batch_size': 32}, 'seed': 123, 'id': 'id4711'}, strict_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({'train': {'lr': 0.01}, 'seed': 123, 'id': 'id4711'}, strict_schema)


def test_union_dict_coercion():
    @deep_dataclass
    class Config:
        @auxiliary
        class TrainMode:
            lr: float = 0.001
            pseudo_batch_size: int = 32

        @auxiliary
        class TestMode:
            metric: str = 'accuracy'
            folds: int = 5

        mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)

    c = Config(mode={'lr': 0.01})
    assert isinstance(c.mode, Config.TrainMode)
    assert c.mode.lr == 0.01
    assert c.mode.pseudo_batch_size == 32

    c = Config(mode={'metric': 'f1', 'folds': 3})
    assert isinstance(c.mode, Config.TestMode)
    assert c.mode.metric == 'f1'
    assert c.mode.folds == 3

    c = Config(mode=Config.TrainMode(lr=0.005))
    assert c.mode.lr == 0.005


@pytest.mark.skipif(sys.version_info < (3, 10), reason='PEP 604 | syntax requires Python 3.10+')
def test_pep604union_dict_coercion():
    @deep_dataclass
    class Config:
        @auxiliary
        class TrainMode:
            lr: float = 0.001
            pseudo_batch_size: int = 32

        @auxiliary
        class TestMode:
            metric: str = 'accuracy'
            folds: int = 5

        mode: TrainMode | TestMode = field(default_factory=TrainMode)

    c = Config(mode={'lr': 0.01})
    assert isinstance(c.mode, Config.TrainMode)
    assert c.mode.lr == 0.01
    assert c.mode.pseudo_batch_size == 32

    c = Config(mode={'metric': 'f1', 'folds': 3})
    assert isinstance(c.mode, Config.TestMode)
    assert c.mode.metric == 'f1'
    assert c.mode.folds == 3

    c = Config(mode=Config.TrainMode(lr=0.005))
    assert c.mode.lr == 0.005
