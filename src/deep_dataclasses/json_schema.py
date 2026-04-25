import dataclasses
import typing


def _type_to_schema(typ, strict: bool = False) -> dict:
    if typ is typing.Any:
        return {}
    if typ is type(None):
        return {"type": "null"}
    if typ is bool:
        return {"type": "boolean"}
    if typ is int:
        return {"type": "integer"}
    if typ is float:
        return {"type": "number"}
    if typ is str:
        return {"type": "string"}
    if dataclasses.is_dataclass(typ):
        return to_json_schema(typ, strict=strict)

    origin = typing.get_origin(typ)
    args = typing.get_args(typ)

    if origin is list:
        return {"type": "array", "items": _type_to_schema(args[0], strict)} if args else {"type": "array"}
    if origin in (set, frozenset):
        return ({"type": "array", "uniqueItems": True, "items": _type_to_schema(args[0], strict)}
                if args else {"type": "array", "uniqueItems": True})
    if origin is tuple:
        if not args:
            return {"type": "array"}
        if len(args) == 2 and args[1] is Ellipsis:
            return {"type": "array", "items": _type_to_schema(args[0], strict)}
        return {
            "type": "array",
            "prefixItems": [_type_to_schema(a, strict) for a in args],
            "minItems": len(args),
            "maxItems": len(args),
        }
    if origin is dict:
        schema = {"type": "object"}
        if len(args) >= 2:
            schema["additionalProperties"] = _type_to_schema(args[1], strict)
        return schema
    if origin is typing.Union:
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and len(args) == 2:
            return {"anyOf": [_type_to_schema(non_none[0], strict), {"type": "null"}]}
        return {"anyOf": [
            to_json_schema(a, strict=strict) if dataclasses.is_dataclass(a) else _type_to_schema(a, strict)
            for a in non_none
        ]}
    if origin is typing.Literal:
        return {"enum": list(args)}

    return {}


def to_json_schema(cls, strict: bool = False, allow_additional_properties: bool = False) -> dict:
    localns = {n: v for n, v in vars(cls).items() if isinstance(v, type)}
    hints = typing.get_type_hints(cls, localns=localns)
    properties = {}
    required = []

    for f in dataclasses.fields(cls):
        typ = hints.get(f.name)
        prop = _type_to_schema(typ, strict) if typ is not None else {}

        if f.default is not dataclasses.MISSING:
            default_val = dataclasses.asdict(f.default) if dataclasses.is_dataclass(f.default) else f.default
            prop = {**prop, "default": default_val}
        elif f.default_factory is not dataclasses.MISSING:
            default_val = f.default_factory()
            if dataclasses.is_dataclass(default_val):
                default_val = dataclasses.asdict(default_val)
            prop = {**prop, "default": default_val}

        has_default = (f.default is not dataclasses.MISSING
                       or f.default_factory is not dataclasses.MISSING)
        is_optional = (
            typ is not None
            and typing.get_origin(typ) is typing.Union
            and type(None) in typing.get_args(typ)
        )
        if not is_optional and (strict or not has_default):
            required.append(f.name)

        properties[f.name] = prop

    schema: dict = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    if not allow_additional_properties:
        schema["additionalProperties"] = False
    return schema
