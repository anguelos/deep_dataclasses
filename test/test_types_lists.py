from __future__ import annotations
import pytest
from dataclasses import dataclass, field, asdict
from deep_dataclasses import deep_dataclass, auxiliary

from typing import List


def test_list_of_dataclasses():
    @deep_dataclass
    class Config:
        @auxiliary
        class Plugin:
            name: str = ""
            enabled: bool = True

        plugins: List[Plugin] = field(default_factory=list)

    # All of these work:
    Config()                                    # plugins=[]
    Config(plugins=[{"name": "foo"}])           # → [Plugin(name="foo", enabled=True)]
    Config(plugins=[Config.Plugin(name="bar")])        # already correct type, passed through
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
