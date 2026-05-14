import dataclasses
import typing

import pytest

from deep_dataclasses import deep_dataclass
from deep_dataclasses.extras import validate_defaults, dataclass_default_can_be_validated


@deep_dataclass
class _ValidCfg:
    x: int = 0
    device: typing.Literal['cpu', 'cuda'] = 'cpu'


@deep_dataclass
class _BadLiteralCfg:
    device: typing.Literal['cpu', 'cuda'] = 'tpu'


@deep_dataclass
class _OptionalCfg:
    x: int = 0
    name: typing.Optional[str] = None


class TestValidateDefaultsHappyPath:
    def test_no_parens(self):
        @validate_defaults
        @deep_dataclass
        class Cfg:
            x: int = 0
        assert Cfg().x == 0

    def test_with_parens(self):
        @validate_defaults()
        @deep_dataclass
        class Cfg:
            x: int = 0
        assert Cfg().x == 0

    def test_strict_true_valid(self):
        @validate_defaults(strict=True)
        @deep_dataclass
        class Cfg:
            x: int = 0
        assert Cfg().x == 0

    def test_strict_false_valid(self):
        @validate_defaults(strict=False)
        @deep_dataclass
        class Cfg:
            x: int = 0
        assert Cfg().x == 0

    def test_optional_field_strict_true(self):
        @validate_defaults(strict=True)
        @deep_dataclass
        class Cfg:
            x: int = 0
            name: typing.Optional[str] = None
        assert Cfg().name is None

    def test_optional_field_strict_false(self):
        @validate_defaults(strict=False)
        @deep_dataclass
        class Cfg:
            x: int = 0
            name: typing.Optional[str] = None
        assert Cfg().name is None


class TestValidateDefaultsRaises:
    def test_bad_literal_raises_type_error(self):
        with pytest.raises(TypeError, match='tpu'):
            @validate_defaults
            @deep_dataclass
            class Cfg:
                device: typing.Literal['cpu', 'cuda'] = 'tpu'

    def test_bad_literal_strict_false_raises_type_error(self):
        with pytest.raises(TypeError):
            @validate_defaults(strict=False)
            @deep_dataclass
            class Cfg:
                device: typing.Literal['cpu', 'cuda'] = 'tpu'

    def test_non_dataclass_raises_value_error(self):
        with pytest.raises(ValueError, match='not a dataclass'):
            @validate_defaults
            class NotADC:
                x: int = 0

    def test_error_message_contains_class_name(self):
        with pytest.raises(TypeError, match='BadCfg'):
            @validate_defaults
            @deep_dataclass
            class BadCfg:
                device: typing.Literal['cpu', 'cuda'] = 'tpu'


class TestValidateDefaultsEnabled:
    def test_enabled_true_validates(self):
        with pytest.raises(TypeError):
            @validate_defaults(enabled=True)
            @deep_dataclass
            class Cfg:
                device: typing.Literal['cpu', 'cuda'] = 'tpu'

    def test_enabled_false_skips_validation(self):
        @validate_defaults(enabled=False)
        @deep_dataclass
        class Cfg:
            device: typing.Literal['cpu', 'cuda'] = 'tpu'
        assert Cfg().device == 'tpu'

    def test_enabled_false_skips_non_dataclass_check(self):
        @validate_defaults(enabled=False)
        class NotADC:
            pass
        assert not dataclasses.is_dataclass(NotADC)

    def test_enabled_true_non_dataclass_raises(self):
        with pytest.raises(ValueError):
            @validate_defaults(enabled=True)
            class NotADC:
                pass


class TestDataclassDefaultCanBeValidated:
    def test_valid_returns_true(self):
        assert dataclass_default_can_be_validated(_ValidCfg) is True

    def test_invalid_literal_returns_false(self):
        assert dataclass_default_can_be_validated(_BadLiteralCfg) is False

    def test_non_dataclass_returns_false(self):
        assert dataclass_default_can_be_validated(int) is False

    def test_strict_true(self):
        assert dataclass_default_can_be_validated(_OptionalCfg, strict=True) is True

    def test_strict_false(self):
        assert dataclass_default_can_be_validated(_OptionalCfg, strict=False) is True


class TestJsonschemaNotInstalled:
    def test_can_be_validated_returns_false_when_no_jsonschema(self, monkeypatch):
        import deep_dataclasses.extras as extras
        monkeypatch.setattr(extras, 'jsonschema', None)
        assert dataclass_default_can_be_validated(_ValidCfg) is False

    def test_validate_defaults_raises_import_error_when_no_jsonschema(self, monkeypatch):
        import deep_dataclasses.extras as extras
        monkeypatch.setattr(extras, 'jsonschema', None)
        with pytest.raises(ImportError, match='jsonschema'):
            @validate_defaults
            @deep_dataclass
            class Cfg:
                x: int = 0

    def test_validate_defaults_enabled_false_skips_import_check(self, monkeypatch):
        import deep_dataclasses.extras as extras
        monkeypatch.setattr(extras, 'jsonschema', None)
        @validate_defaults(enabled=False)
        @deep_dataclass
        class Cfg:
            x: int = 0
        assert Cfg().x == 0
