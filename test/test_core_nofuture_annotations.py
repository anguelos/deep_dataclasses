from dataclasses import asdict, dataclass, field

from deep_dataclasses import deep_dataclass


@dataclass
class _Inner:
    x: int = 0


def test_redecoration_wraps_init():
    @deep_dataclass
    @dataclass
    class Config:
        inner: _Inner = field(default_factory=_Inner)
        name: str = ''

    c = Config(inner={'x': 5}, name='test')
    assert c.inner.x == 5
    assert isinstance(c.inner, _Inner)
    assert Config(**asdict(c)) == c
