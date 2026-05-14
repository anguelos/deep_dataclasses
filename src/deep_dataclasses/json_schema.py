import dataclasses
import typing


def _type_to_schema(typ, strict: bool = False) -> dict:
    if typ is typing.Any:
        return {}
    if typ is type(None):
        return {'type': 'null'}
    if typ is bool:
        return {'type': 'boolean'}
    if typ is int:
        return {'type': 'integer'}
    if typ is float:
        return {'type': 'number'}
    if typ is str:
        return {'type': 'string'}
    if dataclasses.is_dataclass(typ):
        return to_json_schema(typ, strict=strict)

    origin = typing.get_origin(typ)
    args = typing.get_args(typ)

    if origin is list:
        return {'type': 'array', 'items': _type_to_schema(args[0], strict)} if args else {'type': 'array'}
    if origin in (set, frozenset):
        return {'type': 'array', 'uniqueItems': True, 'items': _type_to_schema(args[0], strict)} if args else {'type': 'array', 'uniqueItems': True}
    if origin is tuple:
        if not args:
            return {'type': 'array'}
        if len(args) == 2 and args[1] is Ellipsis:
            return {'type': 'array', 'items': _type_to_schema(args[0], strict)}
        return {
            'type': 'array',
            'prefixItems': [_type_to_schema(a, strict) for a in args],
            'minItems': len(args),
            'maxItems': len(args),
        }
    if origin is dict:
        schema = {'type': 'object'}
        if len(args) >= 2:
            schema['additionalProperties'] = _type_to_schema(args[1], strict)
        return schema
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return {'anyOf': [_type_to_schema(non_none[0], strict), {'type': 'null'}]}
        return {'anyOf': [to_json_schema(a, strict=strict) if dataclasses.is_dataclass(a) else _type_to_schema(a, strict) for a in non_none]}
    if origin is typing.Literal:
        return {'enum': list(args)}

    return {}


def to_json_schema(cls, strict: bool = False, allow_additional_properties: bool = False) -> dict:
    """Generate a JSON Schema ``object`` for a dataclass.

    Recursively converts the field types of *cls* to their JSON Schema
    equivalents.  The resulting schema can be used directly with any
    JSON Schema validator (e.g. ``jsonschema.validate``).

    The following Python types are supported:

    * Primitives: ``bool``, ``int``, ``float``, ``str``, ``None`` /
      ``type(None)``
    * Collections: ``List[T]``, ``Tuple[T, ...]``, ``Tuple[T1, T2, ...]``,
      ``Set[T]``, ``FrozenSet[T]``, ``Dict[K, V]``
    * Composites: ``Optional[T]``, ``Union[A, B, ...]``, ``Literal[...]``
    * Nested dataclasses (recursed automatically)
    * ``typing.Any`` (no constraint)

    Parameters
    ----------
    cls : type
        A ``@dataclass`` or ``@deep_dataclass`` class.
    strict : bool, default False
        When ``False`` (default), only fields without a default value *and*
        not typed as ``Optional`` are listed under ``"required"``.  This
        allows partial dicts to validate successfully as long as omitted
        fields have defaults.

        When ``True``, every field — even those with defaults — is added to
        ``"required"`` unless explicitly typed as ``Optional``.  Use this
        when you want to enforce that all fields are always present.
    allow_additional_properties : bool, default False
        When ``False`` (default), ``"additionalProperties": false`` is
        added to the schema, rejecting any keys not declared as fields.
        This is the right choice for closed schemas such as ``Union``
        variant discrimination.

        When ``True``, extra keys are silently accepted.  Useful when the
        dataclass represents a partial view of a larger document.

    Returns
    -------
    dict
        A JSON Schema ``object`` with the following keys:

        ``"type"``
            Always ``"object"``.
        ``"properties"``
            A dict mapping each field name to its type schema, including a
            ``"default"`` key when the field has a default value or factory.
        ``"required"``
            List of field names that must be present (only included when at
            least one field is required).
        ``"additionalProperties"``
            ``False`` unless *allow_additional_properties* is ``True``.

    Notes
    -----
    The validate-then-construct pattern works end-to-end with
    ``@deep_dataclass`` because construction coerces nested dicts to their
    declared types.  With plain ``@dataclass``, validation succeeds but
    nested dicts are not coerced, so the constructed object may contain raw
    dicts in place of typed fields.

    Examples
    --------
    Basic usage — validate a raw dict before constructing:

    >>> import jsonschema
    >>> from dataclasses import dataclass
    >>> from deep_dataclasses import deep_dataclass, to_json_schema
    >>>
    >>> @deep_dataclass
    ... class Config:
    ...     class Optimizer:
    ...         lr: float = 1e-3
    ...         momentum: float = 0.9
    ...     epochs: int = 100
    >>>
    >>> schema = to_json_schema(Config)
    >>> jsonschema.validate({"Optimizer": {"lr": 0.01}, "epochs": 50}, schema)
    >>> cfg = Config(**{"Optimizer": {"lr": 0.01}, "epochs": 50})
    >>> cfg.Optimizer.lr
    0.01

    ``strict=True`` requires every field to be present, even those with
    defaults:

    >>> strict = to_json_schema(Config, strict=True)
    >>> jsonschema.validate({"epochs": 50}, strict)  # raises — Optimizer missing
    Traceback (most recent call last):
        ...
    jsonschema.exceptions.ValidationError: 'Optimizer' is a required property

    ``allow_additional_properties=True`` accepts extra keys:

    >>> open_schema = to_json_schema(Config, allow_additional_properties=True)
    >>> jsonschema.validate({"epochs": 10, "unknown_key": 42}, open_schema)

    ``Literal`` fields are enforced via ``"enum"``:

    >>> from typing import Literal
    >>>
    >>> @dataclass
    ... class Run:
    ...     device: Literal["cpu", "cuda"] = "cpu"
    >>>
    >>> jsonschema.validate({"device": "tpu"}, to_json_schema(Run))
    Traceback (most recent call last):
        ...
    jsonschema.exceptions.ValidationError: 'tpu' is not valid under any of the given schemas
    """

    localns = {n: v for n, v in vars(cls).items() if isinstance(v, type)}
    hints = typing.get_type_hints(cls, localns=localns)
    properties = {}
    required = []

    for f in dataclasses.fields(cls):
        typ = hints.get(f.name)
        prop = _type_to_schema(typ, strict) if typ is not None else {}

        if f.default is not dataclasses.MISSING:
            default_val = dataclasses.asdict(f.default) if dataclasses.is_dataclass(f.default) else f.default
            prop = {**prop, 'default': default_val}
        elif f.default_factory is not dataclasses.MISSING:
            default_val = f.default_factory()
            if dataclasses.is_dataclass(default_val):
                default_val = dataclasses.asdict(default_val)
            prop = {**prop, 'default': default_val}

        has_default = f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING
        is_optional = typ is not None and typing.get_origin(typ) is typing.Union and type(None) in typing.get_args(typ)
        if not is_optional and (strict or not has_default):
            required.append(f.name)

        properties[f.name] = prop

    schema: dict = {'type': 'object', 'properties': properties}
    if required:
        schema['required'] = required
    if not allow_additional_properties:
        schema['additionalProperties'] = False
    return schema

