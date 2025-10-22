"""Decorators for the fork methods."""

from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


def prefer_transition_to_method(method: F) -> F:
    """Call the `fork_to` implementation when transitioning."""
    method.__prefer_transition_to_method__ = True  # type: ignore
    return method
