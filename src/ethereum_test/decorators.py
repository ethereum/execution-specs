"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, Mapping, cast

from .fill import fill_state_test
from .fork import forks_from
from .state_test import StateTest
from .types import Fixture


def test_from(
    fork: str,
) -> Callable[
    [Callable[[], StateTest]], Callable[[str], Mapping[str, Fixture]]
]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: Callable[[], StateTest]
    ) -> Callable[[str], Mapping[str, Fixture]]:
        def inner(engine) -> Mapping[str, Fixture]:
            return fill_state_test(fn(), forks_from(fork), engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator


def test_only(
    fork: str,
) -> Callable[
    [Callable[[], StateTest]], Callable[[str], Mapping[str, Fixture]]
]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: Callable[[], StateTest]
    ) -> Callable[[str], Mapping[str, Fixture]]:
        def inner(engine) -> Mapping[str, Fixture]:
            return fill_state_test(fn(), [fork], engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator
