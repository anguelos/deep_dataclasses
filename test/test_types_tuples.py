from __future__ import annotations
import pytest
from dataclasses import dataclass, field, asdict
from deep_dataclasses import deep_dataclass, auxiliary
from typing import Tuple


def test_tuple_of_primitives():
    @deep_dataclass
    class Config:
        values: Tuple[int, ...] = field(default_factory=tuple)
    assert len(Config().values) == 0                                 # values=()
    assert len(Config(values=[1, 2, 3]).values) == 3                 # values=(1, 2, 3)
    assert Config(**asdict(Config())) == Config()                    # round-trips through dict
    assert Config(**asdict(Config([1, 2, 3]))) == Config([1, 2, 3])  #  round-trips through dict
    assert "values" in asdict(Config())



def test_tuple_of_dataclasses():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ""
            enabled: bool = True

        plugins: Tuple[Plugin, ...] = field(default_factory=tuple)

    # All of these work:
    Config()                                    # plugins=()
    Config(plugins=[{"name": "foo"}])           # → (Plugin(name="foo", enabled=True),)
    c = Config(plugins=[Config.Plugin(name="bar"), 
                    Config.Plugin(name="other bar"), 
                    Config.Plugin(name="last bar")])
    assert len(c.plugins) == 3
    assert c.plugins[-1].name == "last bar"

    assert Config(plugins=[{"name": "foo"}]).plugins[0].enabled == True
    assert Config(plugins=[{"name": "foo"}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}]).plugins[0].enabled == False
    assert Config(plugins=[{"name": "foo", "enabled": False}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[0].enabled == False
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[1].enabled == True
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[1].name == "bar"
    assert Config(**asdict(Config())) == Config()  # round-trips through dict
    
    # The Plugin class is not a field, so it doesn't appear in the dict representation of Config, but plugins does.
    assert "plugins" in asdict(Config())
    assert "Plugin" not in asdict(Config())


def test_unparameterized_tuple_of_dataclasses():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ""
            enabled: bool = True

        plugins: Tuple[Plugin, Plugin, Plugin] = field(default_factory=tuple)

    # All of these work:
    Config()                                    # plugins=()
    Config(plugins=[{"name": "foo"}])           # → (Plugin(name="foo", enabled=True),)
    c = Config(plugins=[Config.Plugin(name="bar"), 
                    Config.Plugin(name="other bar"), 
                    Config.Plugin(name="last bar")])
    assert len(c.plugins) == 3
    assert c.plugins[-1].name == "last bar"
    c = Config(plugins=[Config.Plugin(name="bar"), 
                        Config.Plugin(name="other bar")])
    assert len(c.plugins) == 2  # Should this be an error? or should a third default plugin be added? 
    # I dont think it should be an error, since we dont validate

    assert Config(plugins=[{"name": "foo"}]).plugins[0].enabled == True
    assert Config(plugins=[{"name": "foo"}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}]).plugins[0].enabled == False
    assert Config(plugins=[{"name": "foo", "enabled": False}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[0].enabled == False
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[0].name == "foo"
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[1].enabled == True
    assert Config(plugins=[{"name": "foo", "enabled": False}, {"name": "bar"}]).plugins[1].name == "bar"
    assert Config(**asdict(Config())) == Config()  # round-trips through dict
    
    # The Plugin class is not a field, so it doesn't appear in the dict representation of Config, but plugins does.
    assert "plugins" in asdict(Config())
    assert "Plugin" not in asdict(Config())
