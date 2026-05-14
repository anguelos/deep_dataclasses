import dataclasses
import re
import typing

# PEP 604: X | Y produces types.UnionType (Python 3.10+), not typing.Union
try:
    from types import UnionType as _UnionType
except ImportError:
    _UnionType = None  # Python < 3.10

# PEP 649: inspect.get_annotations available from Python 3.10+
try:
    from inspect import get_annotations as _get_annotations
except ImportError:

    def _get_annotations(cls):
        return vars(cls).get('__annotations__', {})


TypeForm = typing.Any  # type | GenericAlias | UnionType | None (no stdlib type covers all)

_MUTABLE_COLLECTIONS = (list, dict, set)
_PRIMITIVE_TYPES = (int, str, float, bool, type(None))


def _check_collection_elements(attr_name: str, val: object) -> None:
    if isinstance(val, list):
        bad = [item for item in val if not isinstance(item, _PRIMITIVE_TYPES)]
    elif isinstance(val, dict):
        bad = [k for k in val if not isinstance(k, _PRIMITIVE_TYPES)] + [v for v in val.values() if not isinstance(v, _PRIMITIVE_TYPES)]
    elif isinstance(val, set):
        bad = [item for item in val if not isinstance(item, _PRIMITIVE_TYPES)]
    else:
        return
    if bad:
        raise TypeError(f"field '{attr_name}': default {type(val).__name__} contains non-primitive values {bad!r}. Use field(default_factory=...) explicitly.")


def _wrap_default_mutable_collection(cls, attr_name: str, val: object) -> None:
    if isinstance(val, dataclasses.Field):
        return
    if isinstance(val, _MUTABLE_COLLECTIONS):
        _check_collection_elements(attr_name, val)
        if len(val) == 0:
            setattr(cls, attr_name, dataclasses.field(default_factory=type(val)))
        else:
            setattr(cls, attr_name, dataclasses.field(default_factory=lambda v=val: type(v)(v)))


def auxiliary(cls):
    """Mark a class as a type-only helper inside a ``@deep_dataclass``.

    Decorated inner classes are converted to proper ``@dataclass`` types
    and remain accessible as class attributes, but are **not** promoted to
    standalone fields on the enclosing class.  Use this when an inner class
    is needed purely as a type (e.g. as the element type of a ``List[T]``,
    one arm of a ``Union[A, B]``, or the value type of a ``Dict[K, V]``)
    and should not appear as a default-constructed field in its own right.

    Parameters
    ----------
    cls : type
        The inner class to mark as auxiliary.  Must be a plain class; it
        will be processed by ``@deep_dataclass`` and converted to a
        ``@dataclass`` automatically.

    Returns
    -------
    type
        The same class, with the ``__deep_dataclass_auxiliary__`` attribute
        set to ``True``.

    Notes
    -----
    * ``@auxiliary`` must be applied *before* the enclosing class is
      decorated with ``@deep_dataclass``, i.e. as an inner decorator inside
      the class body.
    * The processed class is still accessible on the enclosing class under
      its original name, so it can be used in type annotations and passed
      to ``isinstance``.

    Examples
    --------
    Using ``@auxiliary`` as an element type for a list field:

    >>> from dataclasses import field
    >>> from typing import List
    >>> from deep_dataclasses import deep_dataclass, auxiliary
    >>>
    >>> @deep_dataclass
    ... class Pipeline:
    ...     @auxiliary
    ...     class Stage:
    ...         name: str = ""
    ...         enabled: bool = True
    ...     stages: List[Stage] = field(default_factory=list)
    >>>
    >>> p = Pipeline(stages=[{"name": "preprocess"}, {"name": "train"}])
    >>> p.stages[0].name
    'preprocess'
    >>> "Stage" in {f.name for f in dataclasses.fields(Pipeline)}
    False

    Using ``@auxiliary`` as a ``Union`` variant:

    >>> from typing import Union
    >>>
    >>> @deep_dataclass
    ... class Config:
    ...     @auxiliary
    ...     class TrainMode:
    ...         lr: float = 1e-3
    ...     @auxiliary
    ...     class TestMode:
    ...         metric: str = "accuracy"
    ...     mode: Union[TrainMode, TestMode] = field(default_factory=TrainMode)
    >>>
    >>> isinstance(Config(mode={"lr": 0.01}).mode, Config.TrainMode)
    True
    """
    cls.__deep_dataclass_auxiliary__ = True
    return cls


def _to_snake(name: str) -> str:
    # PascalCase -> snake_case
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.lower()


def _is_union(typ: TypeForm) -> bool:
    # handles both typing.Union[X, Y] and X | Y (PEP 604)
    return typing.get_origin(typ) is typing.Union or (_UnionType is not None and isinstance(typ, _UnionType))


def _best_union_match(candidates: list, val: dict):
    # return the dataclass from candidates whose fields best cover the keys in val
    best, best_unfilled = None, float('inf')
    for candidate in candidates:
        if dataclasses.is_dataclass(candidate):
            valid = {f.name for f in dataclasses.fields(candidate)}
            if all(k in valid for k in val):
                unfilled = len(valid) - len(val)
                if unfilled < best_unfilled:
                    best, best_unfilled = candidate, unfilled
    return best


def _coerce_value(typ: TypeForm, val: typing.Any) -> typing.Any:
    if val is None or typ is None:
        return val

    origin = typing.get_origin(typ)
    args = typing.get_args(typ)

    # plain dataclass
    if dataclasses.is_dataclass(typ):
        return _coerce_dict_to(typ, val) if isinstance(val, dict) else val

    # Union / Optional[X] / X | Y | None  — all the same branch
    if _is_union(typ):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:  # Optional[X]
            return _coerce_value(non_none[0], val)
        if isinstance(val, dict):  # Union[A, B, ...]
            best = _best_union_match(non_none, val)
            if best is not None:
                return _coerce_dict_to(best, val)
        return val

    if origin is list and args and isinstance(val, (list, tuple)):
        return [_coerce_value(args[0], item) for item in val]

    if origin is tuple and args and isinstance(val, (list, tuple)):
        if len(args) == 2 and args[1] is Ellipsis:  # Tuple[X, ...]
            return tuple(_coerce_value(args[0], item) for item in val)
        return tuple(_coerce_value(et, item) for et, item in zip(args, val))

    if origin is dict and len(args) >= 2 and isinstance(val, dict):
        return {k: _coerce_value(args[1], v) for k, v in val.items()}

    if origin in (set, frozenset) and args and isinstance(val, (list, set, frozenset)):
        return origin(_coerce_value(args[0], item) for item in val)

    return val


def _coerce_dict_to(typ: type, d: dict) -> object:
    # coerce a flat dict into an instance of typ, recursing into each field
    hints = typing.get_type_hints(typ, localns=vars(typ))
    return typ(**{k: _coerce_value(hints.get(k), v) for k, v in d.items()})


def _coerce_fields(instance) -> None:
    # post-init hook: coerce every dict/list/tuple field to its declared type
    cls = type(instance)
    hints = typing.get_type_hints(cls, localns=vars(cls))
    for f in dataclasses.fields(instance):
        val = getattr(instance, f.name)
        coerced = _coerce_value(hints.get(f.name), val)
        if coerced is not val:
            object.__setattr__(instance, f.name, coerced)


def deep_dataclass(cls=None, *, coerce_dicts: bool = True, autosnake: bool = False, **dataclass_kwargs):
    """Class decorator that promotes inner class definitions to ``@dataclass`` fields.

    Each un-annotated inner class whose ``__qualname__`` matches
    ``OuterClass.InnerName`` is recursively processed with
    ``@deep_dataclass`` and promoted to a field whose ``default_factory``
    constructs a default instance.  The result is a fully valid
    ``@dataclass`` compatible with ``dataclasses.asdict``,
    ``dataclasses.fields``, ``repr``, ``==``, and all standard dataclass
    tooling.

    Can be used with or without arguments:

    .. code-block:: python

        @deep_dataclass
        @deep_dataclass()
        @deep_dataclass(autosnake=True, frozen=True)

    Parameters
    ----------
    cls : type, optional
        The class being decorated.  Supplied automatically by Python when
        the decorator is used without parentheses; ``None`` when called
        with keyword arguments.
    coerce_dicts : bool, default True
        When ``True``, injects a ``__post_init__`` hook that recursively
        coerces any ``dict`` argument into its declared dataclass type.
        Coercion descends through:

        - ``SomeDataclass`` — direct coercion.
        - ``Optional[T]`` — coerces the inner type when the value is a dict.
        - ``Union[A, B, ...]`` — selects the dataclass variant whose field
          names cover all keys in the dict, preferring the variant with the
          fewest unfilled fields (exact match wins).
        - ``Dict[K, T]`` — coerces each dict value to ``T``.
        - ``List[T]`` — coerces each list element to ``T``.
        - ``Tuple[T, ...]`` — coerces tuple elements to their declared types.

        A user-defined ``__post_init__`` is preserved and called *after*
        coercion.  Incompatible with ``init=False``.
    autosnake : bool, default False
        When ``True``, PascalCase inner class names are converted to
        snake_case field names (e.g. ``class AdamSolver`` becomes field
        ``adam_solver``).  The original PascalCase name is retained as a
        class attribute so that ``eval(repr(obj))`` round-trips correctly.
    **dataclass_kwargs
        Forwarded verbatim to ``dataclasses.dataclass()``
        (e.g. ``frozen=True``, ``order=True``, ``eq=False``).

    Returns
    -------
    type
        The decorated class as a ``@dataclass`` with all inner classes
        promoted to fields.  If the class was already a ``@dataclass``
        when decorated, its ``__init__`` is wrapped to add coercion rather
        than re-applying ``@dataclass``.

    Raises
    ------
    TypeError
        If ``init=False`` is passed together with ``coerce_dicts=True``.
    TypeError
        If a mutable default value is not a list, dict, or set.
    TypeError
        If a list, dict, or set default contains non-primitive values.
    TypeError
        If a subclass adds mandatory fields after a parent with defaulted fields.

    Notes
    -----
    * Mutable defaults (``list``, ``dict``, ``set``) are automatically
      wrapped with ``field(default_factory=...)``.  Empty containers use
      the type itself as the factory; non-empty containers use a lambda.
      Elements must be primitive types (``int``, ``str``, ``float``,
      ``bool``, ``None``).
    * Inner classes decorated with :func:`auxiliary` are processed and
      kept as class attributes but are **not** promoted to standalone fields.
      Use this for shared type definitions — for example, an element type
      for a ``List[Plugin]`` field — that should not appear on their own.
    * Annotated names (``name: type`` or ``name: type = default``) are
      never treated as inner classes, even when they hold a type value.
    * Fields without defaults (mandatory annotations) are placed before
      fields with defaults, satisfying the restriction imposed by
      ``@dataclass``.
    * ``from __future__ import annotations`` (PEP 563) is fully compatible;
      inner-class type hints are resolved via ``vars(cls)`` at coercion time.

    Examples
    --------
    Basic nested configuration:

    >>> @deep_dataclass
    ... class Config:
    ...     class Optimizer:
    ...         lr: float = 1e-3
    ...         momentum: float = 0.9
    ...     class Scheduler:
    ...         step_size: int = 10
    ...         gamma: float = 0.1
    ...     epochs: int = 100
    >>> Config().Optimizer.lr
    0.001
    >>> Config().epochs
    100

    Mutable defaults are wrapped automatically:

    >>> cfg = Config(Optimizer={"lr": 0.01})
    >>> cfg.Optimizer.lr
    0.01
    >>> isinstance(cfg.Optimizer, Config.Optimizer)
    True

    Round-trip through ``asdict``:

    >>> from dataclasses import asdict
    >>> Config(**asdict(cfg)) == cfg
    True

    ``autosnake`` converts PascalCase inner class names to snake_case fields:

    >>> @deep_dataclass(autosnake=True)
    ... class Model:
    ...     class TransformerEncoder:
    ...         num_layers: int = 6
    >>> Model().transformer_encoder.num_layers
    6
    >>> Model().TransformerEncoder.num_layers   # PascalCase alias preserved
    6

    ``@auxiliary`` marks an inner class as a type helper without creating
    a field for it:

    >>> from typing import List
    >>> from dataclasses import field
    >>> @deep_dataclass
    ... class Experiment:
    ...     tags: list = []
    ...     scores: list = [1, 2, 3]
    ...     meta: dict = {}
    >>> Experiment().tags is Experiment().tags
    False
    """

    def _apply(cls):
        if dataclass_kwargs.get('init') is False and coerce_dicts:
            raise TypeError('coerce_dicts requires init=True')

        user_post_init = vars(cls).get('__post_init__') if coerce_dicts else None
        old_annotations = dict(_get_annotations(cls))

        # wrap mutable collection defaults before @dataclass sees them
        for attr_name in old_annotations:
            val = vars(cls).get(attr_name, dataclasses.MISSING)
            if val is not dataclasses.MISSING:
                _wrap_default_mutable_collection(cls, attr_name, val)

        inner_dcs = {}  # field_name -> dataclass
        pascal_to_field = {}  # PascalCase attr -> field_name (only differs when autosnake=True)

        for attr_name in list(vars(cls)):
            if attr_name.startswith('_'):
                continue
            attr_val = vars(cls)[attr_name]
            is_inner_class = isinstance(attr_val, type) and attr_val.__qualname__ == f'{cls.__qualname__}.{attr_name}' and attr_name not in old_annotations
            if not is_inner_class:
                continue

            inner_dc = deep_dataclass(attr_val, autosnake=autosnake)

            if vars(inner_dc).get('__deep_dataclass_auxiliary__', False):
                # getattr made children of auxiliary to be auxiliaries as well,
                # but we only want to skip the one directly decorated with @auxiliary
                setattr(cls, attr_name, inner_dc)  # type-only helper, no field
            else:
                field_name = _to_snake(attr_name) if autosnake else attr_name
                inner_dcs[field_name] = inner_dc
                pascal_to_field[attr_name] = field_name
                setattr(cls, field_name, dataclasses.field(default_factory=inner_dc))

        # rebuild __annotations__ preserving declaration order;
        # mandatory (no-default) fields first so @dataclass doesn't complain
        ordered, seen = {}, set()
        for key in vars(cls):
            if key.startswith('_'):
                if key in old_annotations:
                    ordered[key] = old_annotations[key]
                    seen.add(key)
                continue
            if key in pascal_to_field:
                fn = pascal_to_field[key]
                ordered[fn] = inner_dcs[fn]
                seen.add(fn)
            elif key in inner_dcs:
                ordered[key] = inner_dcs[key]
                seen.add(key)
            elif key in old_annotations:
                ordered[key] = old_annotations[key]
                seen.add(key)
        mandatory = {k: v for k, v in old_annotations.items() if k not in seen}
        cls.__annotations__ = {**mandatory, **ordered}

        if mandatory:
            #  We can not inherit if there are mandatory fields, because we can't guarantee that the base
            # class defaults won't violate the dataclass field ordering rule.  Check explicitly and error at decoration
            # This is the generic dataclass behavior
            for base in cls.__mro__[1:]:
                if not dataclasses.is_dataclass(base):
                    continue
                for f in dataclasses.fields(base):
                    if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
                        raise TypeError(
                            f"non-default field(s) {list(mandatory)} in '{cls.__name__}' follow "
                            f"default fields inherited from '{base.__name__}'. "
                            f'Use kw_only=True (Python 3.10+) or provide defaults.'
                        )
                        break

        if '__dataclass_fields__' not in vars(cls):  # if not dataclasses.is_dataclass(cls):
            if coerce_dicts:
                if user_post_init:

                    def __post_init__(self):
                        _coerce_fields(self)
                        user_post_init(self)

                    cls.__post_init__ = __post_init__
                else:
                    cls.__post_init__ = _coerce_fields
            cls = dataclasses.dataclass(cls, **dataclass_kwargs)
        else:
            # already a @dataclass or a @dataclass child — wrap __init__
            _orig = cls.__init__

            def __init__(self, *args, **kwargs):
                _orig(self, *args, **kwargs)
                if coerce_dicts:
                    _coerce_fields(self)

            cls.__init__ = __init__

        for field_name, inner_dc in inner_dcs.items():
            setattr(cls, field_name, inner_dc)

        # keep PascalCase aliases so eval(repr(obj)) round-trips
        for pascal_name, field_name in pascal_to_field.items():
            if pascal_name != field_name:
                setattr(cls, pascal_name, inner_dcs[field_name])

        return cls

    return _apply(cls) if cls is not None else _apply
