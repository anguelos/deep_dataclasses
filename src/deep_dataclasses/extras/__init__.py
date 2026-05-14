try:
    import jsonschema
except ImportError:
    jsonschema = None

import dataclasses


from .. import to_json_schema


def dataclass_default_can_be_validated(cls: type, strict: bool = True) -> bool:
    """Return True if the default instance of *cls* passes its own JSON schema.

    Parameters
    ----------
    cls : type
        A dataclass (or deep_dataclass) to check.
    strict : bool
        Passed to :func:`to_json_schema`.  When ``True``, fields without
        defaults are treated as required in the schema.

    Returns
    -------
    bool
        ``False`` if *cls* is not a dataclass, if jsonschema is not installed,
        or if validation fails.
    """
    if not dataclasses.is_dataclass(cls):
        return False
    try:
        schema = to_json_schema(cls, strict=strict)
        jsonschema.validate(instance=dataclasses.asdict(cls()), schema=schema)
        return True
    except Exception:
        return False


def validate_defaults(cls=None, *, strict: bool = True, enabled: bool = __debug__):
    """Decorator that validates the default instance of a dataclass at definition time.

    Raises ``ValueError`` if applied to a non-dataclass.
    Raises ``TypeError`` if the default instance fails schema validation.

    Can be used with or without arguments::

        @validate_defaults
        @deep_dataclass
        class Cfg:
            x: int = 0

        @validate_defaults(strict=False)
        @deep_dataclass
        class Cfg:
            x: int = 0

    Parameters
    ----------
    cls : type, optional
        The class being decorated (supplied automatically when used without parentheses).
    strict : bool
        Passed to :func:`to_json_schema`.  When ``True``, fields without
        defaults are treated as required in the schema.
    enabled : bool
        When ``False`` the decorator is a no-op and returns the class unchanged.
        Defaults to ``__debug__``, so validation is skipped automatically when
        Python is run with ``-O`` / ``PYTHONOPTIMIZE=1``.

    Raises
    ------
    ValueError
        If *cls* is not a dataclass (only raised when *enabled* is ``True``).
    TypeError
        If the default instance of *cls* fails JSON schema validation.
    ImportError
        If jsonschema is not installed and *enabled* is ``True``.
    """
    def _apply(cls):
        if not enabled:
            return cls
        if not dataclasses.is_dataclass(cls):
            raise ValueError(f'{cls!r} is not a dataclass; apply @validate_defaults after @dataclass or @deep_dataclass')
        if jsonschema is None:
            raise ImportError('jsonschema must be installed for validate_defaults to work: pip install deep_dataclasses[extras]')
        schema = to_json_schema(cls, strict=strict)
        try:
            jsonschema.validate(instance=dataclasses.asdict(cls()), schema=schema)
        except jsonschema.ValidationError as e:
            raise TypeError(f'{cls.__name__} default instance failed schema validation: {e.message}') from e
        return cls

    return _apply(cls) if cls is not None else _apply
