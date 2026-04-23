"""deep_dataclass — recursive nested-class to @dataclass transformer.

Converts a plain class hierarchy defined with inner classes into proper
@dataclass instances.  This module has no fargv-specific knowledge; it is a
standalone Python utility.

Declaration order is preserved throughout.  Inner classes become fields with
``default_factory``; annotated attributes become regular fields; annotations
without a default value become mandatory fields (no default).

Only type-valued attributes that were **defined inline** (i.e. ``class``
statements inside the class body, detected via ``__qualname__``) are recursed
into.  Plain assignments (``optimizer = SomeClass``) are ignored.

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

With ``autosnake=True``::

    @deep_dataclass(autosnake=True)
    class Config:
        class MySolver:   # becomes field ``my_solver``
            lr: float = 1e-3
        device: str = "cpu"
"""
import re
import dataclasses
import typing


def _to_snake(name: str) -> str:
    """Convert PascalCase / CamelCase to snake_case."""
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    res = s.lower()
    return res


def _coerce_dict_to(typ: type, d: dict) -> object:
    """Recursively coerce a dict into *typ*, descending into nested dataclass fields."""
    hints = typing.get_type_hints(typ)
    kwargs = {}
    for k, v in d.items():
        ft = hints.get(k)
        kwargs[k] = (_coerce_dict_to(ft, v)
                     if isinstance(v, dict) and ft and dataclasses.is_dataclass(ft)
                     else v)
    return typ(**kwargs)


def _coerce_dicts(self):
    """Coerce dict-valued fields into their declared dataclass types (recursive)."""
    hints = typing.get_type_hints(type(self))
    for f in dataclasses.fields(self):
        val = getattr(self, f.name)
        typ = hints.get(f.name)
        if (isinstance(val, dict)
                and dataclasses.is_dataclass(typ)
                and not isinstance(val, typ)):
            object.__setattr__(self, f.name, _coerce_dict_to(typ, val))


def deep_dataclass(cls=None, *, coerce_dicts: bool = True, autosnake: bool = False, **dataclass_kwargs):
    """Recursively convert a nested class definition into a @dataclass.

    Walks the class in declaration order, transforms inline inner classes
    into ``field(default_factory=...)`` entries, injects ``__post_init__``
    for dict coercion, then calls ``@dataclass`` on the (mutated) class.
    Because the original class is modified in place rather than replaced,
    all existing methods, base classes, properties, and ``field()``
    specifications are preserved exactly as ``@dataclass`` would leave them.

    * **Inline inner classes** (``class`` statements detected via
      ``__qualname__``) are processed recursively and become
      ``field(default_factory=<inner_dc>)`` entries.
    * **Type assignments** (``name = SomeClass``) are silently ignored.
    * Defining ``__post_init__`` on a class passed to ``deep_dataclass``
      raises :class:`TypeError` — it is reserved for dict coercion.

    :param cls:       Class to transform (plain or existing ``@dataclass``).
                      When called as ``@deep_dataclass`` (no arguments), this
                      is the decorated class.  When called as
                      ``@deep_dataclass(autosnake=True)``, this is ``None``
                      and the decorator is returned.
    :param autosnake: When ``True``, PascalCase inner class names are
                      converted to snake_case field names (e.g. ``MySolver``
                      becomes field ``my_solver``).  The original PascalCase
                      name is kept as a class attribute so that
                      ``eval(repr(...))`` still works.
    :param dataclass_kwargs: Extra keyword arguments forwarded to
                      :func:`dataclasses.dataclass` (e.g. ``frozen=True``,
                      ``eq=False``).  ``init=False`` is forbidden because
                      it prevents coercion from running.
    :raises TypeError: When ``__post_init__`` is already defined on *cls*,
                       or when ``init=False`` is passed.
    """
    def _apply(cls):
        if dataclass_kwargs.get("init") is False and coerce_dicts:
            raise TypeError("deep_dataclass requires init=True; when coerce_dicts is True.")
        user_post_init = vars(cls).get("__post_init__") if coerce_dicts else None

        old_annotations = dict(vars(cls).get("__annotations__", {}))
        inner_dcs = {}        # field_name -> dataclass
        pascal_to_field = {}  # PascalCase attr_name -> field_name

        for attr_name in list(vars(cls)):
            if attr_name.startswith("_"):
                continue
            attr_val = vars(cls)[attr_name]
            if (isinstance(attr_val, type)
                    and attr_val.__qualname__ == f"{cls.__qualname__}.{attr_name}"
                    and attr_name not in old_annotations):
                inner_dc = deep_dataclass(attr_val, autosnake=autosnake)
                field_name = _to_snake(attr_name) if autosnake else attr_name
                inner_dcs[field_name] = inner_dc
                pascal_to_field[attr_name] = field_name
                setattr(cls, field_name, dataclasses.field(default_factory=inner_dc))

        # Rebuild __annotations__ in class-body order (vars() order for items
        # present there; mandatory annotation-only fields prepended so that
        # @dataclass sees no-default fields before defaulted ones).
        ordered, seen = {}, set()
        for key in vars(cls):
            if key.startswith("_"):
                if key in old_annotations:
                    ordered[key] = old_annotations[key]
                    seen.add(key)
                continue
            if key in pascal_to_field:
                fn = pascal_to_field[key]
                ordered[fn] = inner_dcs[fn]; seen.add(fn)
            elif key in inner_dcs:
                ordered[key] = inner_dcs[key]; seen.add(key)
            elif key in old_annotations:
                ordered[key] = old_annotations[key]; seen.add(key)
        mandatory = {k: v for k, v in old_annotations.items() if k not in seen}
        cls.__annotations__ = {**mandatory, **ordered}

        if not dataclasses.is_dataclass(cls):
            if coerce_dicts:
                if user_post_init:
                    def __post_init__(self):
                        _coerce_dicts(self)
                        user_post_init(self)
                    cls.__post_init__ = __post_init__
                else:
                    cls.__post_init__ = _coerce_dicts
            # else: no injection, user's __post_init__ (if any) stays
            cls = dataclasses.dataclass(cls, **dataclass_kwargs)
        else:
            # already a @dataclass — wrap __init__ instead
            _orig = cls.__init__
            if coerce_dicts:
                def __init__(self, *args, **kwargs):
                    _orig(self, *args, **kwargs)
                    _coerce_dicts(self)
            cls.__init__ = __init__

        for field_name, inner_dc in inner_dcs.items():
            setattr(cls, field_name, inner_dc)

        # Keep PascalCase names as class attrs so eval(repr(...)) works
        for pascal_name, field_name in pascal_to_field.items():
            if pascal_name != field_name:
                setattr(cls, pascal_name, inner_dcs[field_name])

        return cls

    if cls is None:
        # Called as @deep_dataclass(autosnake=True) — return decorator
        return _apply
    else:
        # Called as @deep_dataclass (no arguments)
        return _apply(cls)
