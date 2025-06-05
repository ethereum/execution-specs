"""
Dataclass extension that supports immutability.
"""

from dataclasses import is_dataclass, replace
from functools import wraps
from typing import (
    Any,
    Callable,
    Concatenate,
    ParamSpec,
    Protocol,
    TypeVar,
    runtime_checkable,
)


@runtime_checkable
class SlottedFreezable(Protocol):
    """
    A [`Protocol`] implemented by data classes annotated with
    [`@slotted_freezable`].

    [`@slotted_freezable`]: ref:ethereum_types.frozen.slotted_freezable
    [`Protocol`]: https://docs.python.org/library/typing.html#typing.Protocol
    """

    _frozen: bool


def _setattr_function(self: Any, attr: str, value: Any) -> None:
    if getattr(self, "_frozen", None):
        raise AttributeError("Mutating frozen dataclasses is not allowed.")
    else:
        object.__setattr__(self, attr, value)


def _delattr_function(self: Any, attr: str) -> None:
    if self._frozen:
        raise AttributeError("Mutating frozen dataclasses is not allowed.")
    else:
        object.__delattr__(self, attr)


_S = TypeVar("_S", bound=SlottedFreezable)
_P = ParamSpec("_P")


def _make_init_function(
    f: Callable[Concatenate[_S, _P], None]
) -> Callable[Concatenate[_S, _P], None]:
    @wraps(f)
    def init_function(self: _S, *args: _P.args, **kwargs: _P.kwargs) -> None:
        will_be_frozen = kwargs.pop("_frozen", True)
        assert isinstance(will_be_frozen, bool)
        object.__setattr__(self, "_frozen", False)
        f(self, *args, **kwargs)
        self._frozen = will_be_frozen

    return init_function


def slotted_freezable(cls: Any) -> Any:
    """
    Monkey patches a dataclass so it can be frozen by setting `_frozen` to
    `True` and uses `__slots__` for efficiency.

    Instances will be created frozen by default unless you pass `_frozen=False`
    to `__init__`.
    """
    cls.__slots__ = ("_frozen",) + tuple(cls.__annotations__)
    cls.__init__ = _make_init_function(cls.__init__)
    cls.__setattr__ = _setattr_function
    cls.__delattr__ = _delattr_function
    return type(cls)(cls.__name__, cls.__bases__, dict(cls.__dict__))


S = TypeVar("S")


def modify(obj: S, f: Callable[[S], None]) -> S:
    """
    Create a copy of `obj` (which must be [`@slotted_freezable`]), and modify
    it by applying `f`. The returned copy will be frozen.

    [`@slotted_freezable`]: ref:ethereum_types.frozen.slotted_freezable
    """
    assert is_dataclass(obj)
    assert isinstance(obj, SlottedFreezable)
    new_obj = replace(obj, _frozen=False)  # type: ignore[unreachable]
    f(new_obj)
    new_obj._frozen = True
    return new_obj
