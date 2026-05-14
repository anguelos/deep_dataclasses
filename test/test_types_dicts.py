from __future__ import annotations

from dataclasses import asdict, field
from typing import Dict

from deep_dataclasses import auxiliary, deep_dataclass


def test_dict_of_dataclasses():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ''
            enabled: bool = True

        plugins: Dict[str, Plugin] = field(default_factory=dict)

    # All of these work:
    Config()  # plugins={}
    Config(plugins={'foo': {'name': 'foo'}})  # → {"foo": Plugin(name="foo", enabled=True)}
    Config(plugins={'bar': Config.Plugin(name='bar'), 'shop': {'name': 'shop'}})  # already correct type, passed through
    assert Config(plugins={'foo': {'name': 'foo'}}).plugins['foo'].enabled == True

    assert Config(plugins={'foo': {'name': 'foo'}}).plugins['foo'].name == 'foo'
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}}).plugins['foo'].enabled == False
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}}).plugins['foo'].name == 'foo'
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}, 'bar': {'name': 'bar'}}).plugins['foo'].enabled == False
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}, 'bar': {'name': 'bar'}}).plugins['foo'].name == 'foo'
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}, 'bar': {'name': 'bar'}}).plugins['bar'].enabled == True
    assert Config(plugins={'foo': {'name': 'foo', 'enabled': False}, 'bar': {'name': 'bar'}}).plugins['bar'].name == 'bar'
    assert Config(**asdict(Config())) == Config()  # round-trips through dict

    # The Plugin class is not a field, so it doesn't appear in the dict representation of Config, but plugins does.
    assert 'plugins' in asdict(Config())
    assert 'Plugin' not in asdict(Config())


def test_unparameterized_dict_passthrough():
    @deep_dataclass
    class Config:
        data: dict = field(default_factory=dict)

    c = Config(data={'a': 1, 'b': 'hello'})
    assert c.data == {'a': 1, 'b': 'hello'}
    assert Config().data == {}
