"""
deep_dataclasses
================

Define nested dataclass hierarchies as readable inline schemas — no
boilerplate, no mandatory dependencies.

``deep_dataclasses`` is a pure-Python package (``re``, ``dataclasses``,
``typing`` only) that lets you write nested ``@dataclass`` hierarchies as
natural indented class blocks.  The decorator infers the class name, type
hint, and ``default_factory`` from the nested block, eliminating the
three-fold repetition required by ``@dataclass`` alone.  The result is a
fully standard dataclass, compatible with ``dataclasses.asdict``,
``dataclasses.fields``, ``repr``, ``==``, ``frozen``, ``slots``, and all
other stdlib tooling.

Source code and issue tracker:
`https://github.com/anguelos/deep_dataclasses
<https://github.com/anguelos/deep_dataclasses>`_

Public API
----------

.. autosummary::
   :nosignatures:

   deep_dataclass
   auxiliary
   to_json_schema

deep_dataclass
    Class decorator.  Promotes inner class definitions to ``@dataclass``
    fields, recursively.  Injects dict-to-instance coercion at
    construction time so that ``cls(**dataclasses.asdict(instance)) ==
    instance`` holds at all nesting depths.

auxiliary
    Class decorator.  Marks an inner class as a type-only helper —
    converted to a ``@dataclass`` and kept as a class attribute, but
    **not** promoted to a standalone field.  Use for ``List[T]``,
    ``Union[A, B]``, ``Dict[K, V]`` element types.

to_json_schema
    Exports a ``@dataclass`` or ``@deep_dataclass`` as a JSON Schema
    ``object`` dict, suitable for use with ``jsonschema.validate``.
    Supports ``strict`` (require all fields) and
    ``allow_additional_properties`` parameters.

Examples
--------
Nested configuration with automatic ``default_factory`` wiring:

>>> from deep_dataclasses import deep_dataclass
>>>
>>> @deep_dataclass
... class Config:
...     class Optimizer:
...         lr: float = 1e-3
...         momentum: float = 0.9
...     epochs: int = 100
>>>
>>> Config().Optimizer.lr
0.001
>>> Config().epochs
100

Dict coercion — pass nested dicts instead of instances:

>>> cfg = Config(Optimizer={"lr": 0.01})
>>> cfg.Optimizer.lr
0.01
>>> import dataclasses
>>> Config(**dataclasses.asdict(cfg)) == cfg
True

Type-only helpers with ``@auxiliary``:

>>> from dataclasses import field
>>> from typing import Union
>>> from deep_dataclasses import auxiliary
>>>
>>> @deep_dataclass
... class Experiment:
...     @auxiliary
...     class TrainMode:
...         lr: float = 1e-3
...     @auxiliary
...     class TestMode:
...         metric: str = "accuracy"
...     mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)
>>>
>>> e = Experiment(mode={"metric": "f1"})
>>> isinstance(e.mode, Experiment.TestMode)
True

Schema validation before construction:

>>> import jsonschema
>>> from deep_dataclasses import to_json_schema
>>>
>>> schema = to_json_schema(Config)
>>> jsonschema.validate({"Optimizer": {"lr": 0.05}, "epochs": 10}, schema)
>>> jsonschema.validate({"Optimizer": {"lr": "bad"}}, schema)
Traceback (most recent call last):
    ...
jsonschema.exceptions.ValidationError: 'bad' is not of type 'number'
"""


from .deep_dataclass import deep_dataclass, auxiliary
from .json_schema import to_json_schema

__version__ = "0.3.3"

__all__ = ["deep_dataclass", "auxiliary", "to_json_schema", "__version__"]
