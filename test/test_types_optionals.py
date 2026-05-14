from __future__ import annotations

import sys
from dataclasses import asdict
from typing import Optional

import pytest

from deep_dataclasses import auxiliary, deep_dataclass


def test_optional_none_default():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ''
            enabled: bool = True

        plugin: Optional[Plugin] = None

    assert Config().plugin is None
    assert Config(plugin=None).plugin is None


def test_optional_dict_coercion():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ''
            enabled: bool = True

        plugin: Optional[Plugin] = None

    c = Config(plugin={'name': 'foo'})
    assert isinstance(c.plugin, Config.Plugin)
    assert c.plugin.name == 'foo'
    assert c.plugin.enabled == True

    c = Config(plugin={'name': 'bar', 'enabled': False})
    assert c.plugin.name == 'bar'
    assert c.plugin.enabled == False


def test_optional_instance_passthrough():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ''
            enabled: bool = True

        plugin: Optional[Plugin] = None

    p = Config.Plugin(name='baz', enabled=False)
    assert Config(plugin=p).plugin is p


def test_optional_roundtrip():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ''
            enabled: bool = True

        plugin: Optional[Plugin] = None

    assert Config(**asdict(Config())) == Config()
    assert Config(**asdict(Config(plugin={'name': 'x'}))) == Config(plugin=Config.Plugin(name='x'))


def test_optional_inner_class_as_field():
    @deep_dataclass
    class Config:
        class solver:
            lr: float = 1e-3
            momentum: float = 0.9

        extra: Optional[str] = None

    assert Config().extra is None
    assert Config(extra='hello').extra == 'hello'
    assert Config(**asdict(Config())) == Config()
    assert Config(**asdict(Config(extra='hello'))) == Config(extra='hello')


def test_optional_nested_deep_dataclass():
    @deep_dataclass
    class Config:
        @auxiliary
        class Metrics:
            accuracy: float = 0.0
            loss: float = 0.0

        class solver:
            lr: float = 1e-3

        metrics: Optional[Metrics] = None

    assert Config().metrics is None
    c = Config(metrics={'accuracy': 0.95, 'loss': 0.05})
    assert isinstance(c.metrics, Config.Metrics)
    assert c.metrics.accuracy == 0.95
    assert Config(**asdict(Config())) == Config()
    assert Config(**asdict(Config(metrics={'accuracy': 0.9}))) == Config(metrics=Config.Metrics(accuracy=0.9))


@pytest.mark.skipif(sys.version_info < (3, 10), reason='PEP 604 | syntax requires Python 3.10+')
def test_pep604optional_nested_deep_dataclass():
    @deep_dataclass
    class Config:
        @auxiliary
        class Metrics:
            accuracy: float = 0.0
            loss: float = 0.0

        class solver:
            lr: float = 1e-3

        metrics: Metrics | None = None

    assert Config().metrics is None
    c = Config(metrics={'accuracy': 0.95, 'loss': 0.05})
    print(f'Metrics: {c.metrics}')
    assert isinstance(c.metrics, Config.Metrics)
    assert c.metrics.accuracy == 0.95
    assert Config(**asdict(Config())) == Config()
    assert Config(**asdict(Config(metrics={'accuracy': 0.9}))) == Config(metrics=Config.Metrics(accuracy=0.9))


def test_optional_primitive_fields():
    @deep_dataclass
    class Config:
        name: Optional[str] = None
        count: Optional[int] = None
        ratio: Optional[float] = None

    assert Config().name is None
    assert Config(name='x', count=3, ratio=0.5) == Config(name='x', count=3, ratio=0.5)
    assert Config(**asdict(Config(name='y'))) == Config(name='y')
