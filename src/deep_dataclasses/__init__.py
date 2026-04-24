"""deep_dataclass — recursive nested-class to @dataclass transformer.

Converts a plain class hierarchy defined with inner classes into proper
@dataclass instances.  This module  is a standalone Python utility.

Declaration order is preserved throughout.  Inner classes become fields with
``default_factory``; annotated attributes become regular fields; annotations
without a default value become mandatory fields (no default).

Example::

    @deep_dataclass
    class Config:
        class Solver:
            class Adam:
                lr: float = 1e-3
                beta1: float = 0.9
            class SGD:
                lr: float = 0.1
                momentum: float = 0.9
        device: str = "cpu"
        seed: int = 42

    # Config is a @dataclass with fields:
    #   Solver: <Solver dataclass>  (default_factory=Solver)
    #   device: str = "cpu"
    #   seed:   int = 42
    #
    # Config.Solver is a @dataclass with fields:
    #   Adam: <Adam dataclass>  (default_factory=Adam)
    #   SGD:  <SGD dataclass>   (default_factory=SGD)
"""

from .deep_dataclass import deep_dataclass, auxiliary
from .json_schema import to_json_schema

__version__ = "0.3.1"

__all__ = ["deep_dataclass", "auxiliary", "to_json_schema", "__version__"]
