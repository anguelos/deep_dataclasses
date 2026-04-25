import re
import dataclasses
import typing


# part of addressing PEP 649 -- in Python 3.10+ we can just use get_annotations with eval_str=True, 
# but for 3.8/3.9 we need to resolve the annotations ourselves at coercion time.
try:
    from inspect import get_annotations as _get_cls_annotations
except ImportError:
    def _get_cls_annotations(cls):  # Python 3.8 / 3.9
        return vars(cls).get('__annotations__', {})


def auxiliary(cls):
    """Mark a class as auxiliary, i.e. to be used as a nested dataclass but not promoted to a field on the parent. Usefull for defining lists of classes etc."""
    cls.__deep_dataclass_auxiliary__ = True
    return cls


def _to_snake(name: str) -> str:
    """Convert PascalCase / CamelCase to snake_case."""
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
    return s.lower()


def _get_list_element_type(typ):
    if typing.get_origin(typ) is list:
        args = typing.get_args(typ)
        return args[0] if args else None
    return None


def _get_tuple_element_types(typ):
    if typing.get_origin(typ) is tuple:
        args = typing.get_args(typ)
        return args if args else None
    return None


def _get_dict_value_type(typ):
    if typing.get_origin(typ) is dict:
        args = typing.get_args(typ)
        return args[1] if len(args) >= 2 else None
    return None


def _unwrap_optional(typ):
    """Return the inner type of Optional[T] / Union[T, None], or None."""
    if typing.get_origin(typ) is typing.Union:
        args = [a for a in typing.get_args(typ) if a is not type(None)]
        if len(args) == 1:
            return args[0]
    return None


def _resolve_union_dataclass(typ, val: dict):
    """Return the first Union member that is a dataclass whose fields cover all keys in val, or None."""
    if typing.get_origin(typ) is not typing.Union:
        return None
    
    # If it's a Union, find the dataclass type among the options that best matches the keys in val.
    # Covering more keys is better, but we also want to prefer fewer unmatched required fields, 
    # so we take the one with the best coverage ratio and then break ties by fewest unfilled fields.
    best, best_unfilled = None, float('inf')
    for arg in typing.get_args(typ):
        if dataclasses.is_dataclass(arg):
            valid = {f.name for f in dataclasses.fields(arg)}
            if all(k in valid for k in val):
                unfilled = len(valid) - len(val)
                if unfilled < best_unfilled:
                    best, best_unfilled = arg, unfilled
    return best


def _coerce_tuple(elem_types, val):
    if len(elem_types) == 2 and elem_types[1] is Ellipsis:
        et = elem_types[0]
        if dataclasses.is_dataclass(et):
            return tuple(_coerce_dict_to(et, item) if isinstance(item, dict) else item for item in val)
        return tuple(val)
    return tuple(
        _coerce_dict_to(et, item) if dataclasses.is_dataclass(et) and isinstance(item, dict) else item
        for et, item in zip(elem_types, val)
    )


def _coerce_dict_to(typ: type, d: dict) -> object:
    """Recursively coerce a dict into *typ*, descending into nested dataclass fields."""
    hints = typing.get_type_hints(typ, localns=vars(typ))
    kwargs = {}
    for k, v in d.items():
        ft = hints.get(k)
        if isinstance(v, dict) and ft and dataclasses.is_dataclass(ft):
            kwargs[k] = _coerce_dict_to(ft, v)
        elif isinstance(v, dict) and ft is not None:
            inner = _unwrap_optional(ft)
            if inner is not None and dataclasses.is_dataclass(inner):
                kwargs[k] = _coerce_dict_to(inner, v)
            else:
                union_dc = _resolve_union_dataclass(ft, v)
                if union_dc is not None:
                    kwargs[k] = _coerce_dict_to(union_dc, v)
                else:
                    dict_vt = _get_dict_value_type(ft)
                    if dict_vt is not None and dataclasses.is_dataclass(dict_vt):
                        kwargs[k] = {kk: _coerce_dict_to(dict_vt, vv) if isinstance(vv, dict) else vv for kk, vv in v.items()}
                    else:
                        kwargs[k] = v
        elif isinstance(v, (list, tuple)) and ft is not None:
            elem_type = _get_list_element_type(ft)
            elem_types = _get_tuple_element_types(ft)
            if elem_type is not None and dataclasses.is_dataclass(elem_type):
                kwargs[k] = [
                    _coerce_dict_to(elem_type, item) if isinstance(item, dict) else item
                    for item in v
                ]
            elif elem_types is not None:
                kwargs[k] = _coerce_tuple(elem_types, v)
            else:
                kwargs[k] = v
        else:
            kwargs[k] = v
    return typ(**kwargs)


def _coerce_dicts(self):
    """Coerce dict-valued fields into their declared dataclass types (recursive)."""
    cls = type(self)
    hints = typing.get_type_hints(cls, localns=vars(cls))  
    for f in dataclasses.fields(self):
        val = getattr(self, f.name)
        typ = hints.get(f.name)

        if isinstance(val, dict) and dataclasses.is_dataclass(typ):
            object.__setattr__(self, f.name, _coerce_dict_to(typ, val))
        elif isinstance(val, dict) and typ is not None:
            inner = _unwrap_optional(typ)
            if inner is not None and dataclasses.is_dataclass(inner):
                object.__setattr__(self, f.name, _coerce_dict_to(inner, val))
            else:
                union_dc = _resolve_union_dataclass(typ, val)
                if union_dc is not None:
                    object.__setattr__(self, f.name, _coerce_dict_to(union_dc, val))
                else:
                    dict_vt = _get_dict_value_type(typ)
                    if dict_vt is not None and dataclasses.is_dataclass(dict_vt):
                        object.__setattr__(self, f.name, {kk: _coerce_dict_to(dict_vt, vv) if isinstance(vv, dict) else vv for kk, vv in val.items()})
                    else:
                        object.__setattr__(self, f.name, val)

        elif isinstance(val, (list, tuple)) and typ is not None:
            elem_type = _get_list_element_type(typ)
            elem_types = _get_tuple_element_types(typ)
            if elem_type is not None and dataclasses.is_dataclass(elem_type):
                object.__setattr__(self, f.name, [
                    _coerce_dict_to(elem_type, item) if isinstance(item, dict) else item
                    for item in val
                ])
            elif elem_types is not None:
                object.__setattr__(self, f.name, _coerce_tuple(elem_types, val))


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

    Notes
    -----
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

    Passing dicts instead of instances (coerce_dicts):

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
    ... class Pipeline:
    ...     @auxiliary
    ...     class Stage:
    ...         name: str = ""
    ...         enabled: bool = True
    ...     stages: List[Stage] = field(default_factory=list)
    >>> p = Pipeline(stages=[{"name": "preprocess"}, {"name": "train"}])
    >>> p.stages[0].name
    'preprocess'
    >>> "Stage" in {f.name for f in dataclasses.fields(Pipeline)}
    False
    """
    def _apply(cls):
        if dataclass_kwargs.get("init") is False and coerce_dicts:
            raise TypeError("deep_dataclass requires init=True; when coerce_dicts is True.")
        user_post_init = vars(cls).get("__post_init__") if coerce_dicts else None

        old_annotations = dict(_get_cls_annotations(cls))

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

                if getattr(inner_dc, "__deep_dataclass_auxiliary__", False):
                    # Type-only helper — no standalone field
                    setattr(cls, attr_name, inner_dc)
                else:
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
