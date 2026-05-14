from __future__ import annotations

import sys
from typing import Optional, Union

enable_future_annotations = True


from dataclasses import dataclass, field, make_dataclass
from typing import Any, Dict, List, Literal, Set, Tuple

import jsonschema
import pytest

from deep_dataclasses import deep_dataclass, to_json_schema


def test_simple_dataclass():
    @dataclass
    class Config:
        lr: float = 1e-3
        beta1: float = 0.9
        momentum: float = 0.9
        device: str = 'cpu'
        seed: Optional[int] = 42

    schema = to_json_schema(Config)
    assert schema['type'] == 'object'
    assert 'lr' in schema['properties']
    assert 'beta1' in schema['properties']
    assert 'momentum' in schema['properties']
    assert 'device' in schema['properties']
    assert 'seed' in schema['properties']

    strict_schema = to_json_schema(Config, strict=True)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'lr': 0.01, 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'lr': 'not_a_float', 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({'lr': 0.01, 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda'}, strict_schema)


def test_simple_deep_dataclass():
    @deep_dataclass
    class Config:
        lr: float = 1e-3
        beta1: float = 0.9
        momentum: float = 0.9
        device: str = 'cpu'
        seed: Optional[int] = 42

    schema = to_json_schema(Config)
    assert schema['type'] == 'object'
    assert 'lr' in schema['properties']
    assert 'beta1' in schema['properties']
    assert 'momentum' in schema['properties']
    assert 'device' in schema['properties']
    assert 'seed' in schema['properties']

    strict_schema = to_json_schema(Config, strict=True)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'lr': 0.01, 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'lr': 'not_a_float', 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda', 'seed': 123}, strict_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({'lr': 0.01, 'beta1': 0.8, 'momentum': 0.95, 'device': 'cuda'}, strict_schema)


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
    assert schema['type'] == 'object'
    assert 'train' in schema['properties']
    assert 'seed' in schema['properties']

    strict_schema = to_json_schema(Config, strict=True)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'train': {'lr': 0.01, 'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'lr': 'not_a_float', 'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({'train': {'lr': 0.01}, 'seed': 123}, strict_schema)


def test_deep_dataclass():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32

        seed: int = 42

    schema = to_json_schema(Config)
    assert schema['type'] == 'object'
    assert 'train' in schema['properties']
    assert 'seed' in schema['properties']

    strict_schema = to_json_schema(Config, strict=True)
    # correct — jsonschema validates it without raising an error
    jsonschema.validate({'train': {'lr': 0.01, 'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # wrong type — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'lr': 'not_a_float', 'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # missing field — jsonschema raises ValidationError
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({'train': {'pseudo_batch_size': 32}, 'seed': 123}, strict_schema)

    # missing optional field — jsonschema allows it and doesn't raise an error
    jsonschema.validate({'train': {'lr': 0.01}, 'seed': 123}, strict_schema)


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
        id: Union[int, str] = 'id123'

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


@pytest.mark.skipif(sys.version_info < (3, 10), reason='PEP 604 | syntax requires Python 3.10+')
def test_pep604unions():
    @deep_dataclass
    class Config:
        class train:
            lr: float = 1e-3
            pseudo_batch_size: Optional[int] = 32

        seed: int = 42
        id: int | str = 'id123'

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


def test_type_zoo():
    @dataclass
    class Config:
        flag: bool = True
        tags: List[str] = field(default_factory=list)
        mapping: Dict[str, int] = field(default_factory=dict)
        unique: Set[str] = field(default_factory=set)
        pair: Tuple[int, str] = field(default_factory=lambda: (0, ''))
        variable: Tuple[float, ...] = field(default_factory=tuple)
        empty_tup: Tuple = field(default_factory=tuple)
        mode: Literal['train', 'test'] = 'train'
        anything: Any = None
        raw: list = field(default_factory=list)

    schema = to_json_schema(Config)
    p = schema['properties']

    assert p['flag']['type'] == 'boolean'
    assert p['tags']['type'] == 'array'
    assert p['tags']['items'] == {'type': 'string'}
    assert p['mapping']['type'] == 'object'
    assert p['mapping']['additionalProperties'] == {'type': 'integer'}
    assert p['unique']['type'] == 'array'
    assert p['unique']['uniqueItems'] is True
    assert p['unique']['items'] == {'type': 'string'}
    assert p['pair']['type'] == 'array'
    assert len(p['pair']['prefixItems']) == 2
    assert p['variable']['type'] == 'array'
    assert 'items' in p['variable']
    assert p['empty_tup'] == {'type': 'array', 'default': ()}
    assert p['mode']['enum'] == ['train', 'test']
    assert 'type' not in p['anything']
    assert 'type' not in p['raw']


def test_null_type():
    NullConfig = make_dataclass('NullConfig', [('nothing', type(None), field(default=None))])
    schema = to_json_schema(NullConfig)
    assert schema['properties']['nothing']['type'] == 'null'
