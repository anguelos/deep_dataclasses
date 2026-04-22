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
import dataclasses
import typing


class DictCoercible:
    """Mixin that coerces dict arguments into nested dataclass instances.

    Applied automatically by :func:`deep_dataclass` to every generated class.
    When a field typed as a dataclass receives a plain ``dict`` value,
    ``__post_init__`` converts it via ``FieldType(**the_dict)``, which in turn
    triggers the same coercion one level deeper.

    Existing dataclass instances pass through unchanged.
    """

    def __post_init__(self):
        hints = typing.get_type_hints(type(self))
        for f in dataclasses.fields(self):
            val = getattr(self, f.name)
            typ = hints.get(f.name)
            if (isinstance(val, dict)
                    and dataclasses.is_dataclass(typ)
                    and not isinstance(val, typ)):
                object.__setattr__(self, f.name, typ(**val))


def deep_dataclass(cls=None, *, exclude_from_recursion=()):
    """Recursively convert a nested class definition into a @dataclass.

    May be used with or without arguments::

        @deep_dataclass
        class Config: ...

        @deep_dataclass(exclude_from_recursion=["Config.optimizer"])
        class Config: ...

    Walks ``cls.__dict__`` in declaration order:

    * **Inner classes** (unannotated ``type``-valued attributes not listed in
      *exclude_from_recursion*) are processed recursively and become
      ``field(default_factory=<inner_dc>)`` entries.
    * **Annotated attributes with a default** become ``field(default=value)``.
    * **Annotated attributes without a default** become mandatory fields.
    * **Excluded attributes** are silently dropped (not recursed, not a field).

    :param cls:                   Class to transform (when used without arguments).
    :param exclude_from_recursion: Strings of the form ``"ClassName.attr"``
                                  identifying type-valued attributes that should
                                  not be treated as inner-class branches.
                                  Each string must resolve to an actual ``type``
                                  attribute on the named class; unmatched entries
                                  raise :class:`ValueError`.
    :raises TypeError:  When *cls* is already a ``@dataclass``.
    :raises ValueError: When an exclusion string matches nothing in the hierarchy.
    """
    exclusions = list(exclude_from_recursion)

    def _apply(c, used):
        if dataclasses.is_dataclass(c):
            return c
        excluded = set()
        for excl in exclusions:
            cname, _, attr = excl.rpartition(".")
            if cname == c.__name__:
                if not isinstance(vars(c).get(attr), type):
                    raise ValueError(
                        f"exclude_from_recursion {excl!r}: {attr!r} is not a "
                        f"type attribute of class {c.__name__!r}"
                    )
                excluded.add(attr)
                used.add(excl)

        annotations = vars(c).get("__annotations__", {})
        fields = []
        seen = set()
        for attr_name, attr_val in vars(c).items():
            if attr_name.startswith("_"):
                continue
            if (isinstance(attr_val, type)
                    and attr_name not in annotations
                    and attr_name not in excluded):
                inner_dc = _apply(attr_val, used)
                fields.append((attr_name, inner_dc, dataclasses.field(default_factory=inner_dc)))
                seen.add(attr_name)
            elif attr_name in annotations:
                fields.append((attr_name, annotations[attr_name], dataclasses.field(default=attr_val)))
                seen.add(attr_name)
        for attr_name, field_type in annotations.items():
            if attr_name not in seen:
                fields.append((attr_name, field_type))
        return dataclasses.make_dataclass(
            c.__name__,
            fields,
            bases=(DictCoercible,),
            namespace={"__module__":   getattr(c, "__module__",   __name__),
                       "__qualname__": getattr(c, "__qualname__", c.__name__)},
        )

    def _decorate(c):
        if dataclasses.is_dataclass(c):
            raise TypeError(
                f"deep_dataclass requires a plain class, got an existing @dataclass: {c!r}"
            )
        used = set()
        result = _apply(c, used)
        unused = [e for e in exclusions if e not in used]
        if unused:
            raise ValueError(
                f"exclude_from_recursion entries matched nothing in the class hierarchy: {unused}"
            )
        return result

    return _decorate(cls) if cls is not None else _decorate


__all__ = ["deep_dataclass"]