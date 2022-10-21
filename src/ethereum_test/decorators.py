"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, Mapping, cast

from .fill import fill_state_test
from .fork import forks_from, forks_from_until
from .state_test import StateTestSpec
from .types import Fixture


def test_from_until(
    fork_from: str,
    fork_until: str,
) -> Callable[[StateTestSpec], Callable[[str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork_from = fork_from.capitalize()
    fork_until = fork_until.capitalize()

    def decorator(fn: StateTestSpec) -> Callable[[str], Mapping[str, Fixture]]:
        def inner(engine) -> Mapping[str, Fixture]:
            return fill_state_test(
                fn, forks_from_until(fork_from, fork_until), engine
            )

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork_from,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator


def test_from(
    fork: str,
) -> Callable[[StateTestSpec], Callable[[str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork = fork.capitalize()

    def decorator(fn: StateTestSpec) -> Callable[[str], Mapping[str, Fixture]]:
        def inner(engine) -> Mapping[str, Fixture]:
            return fill_state_test(fn, forks_from(fork), engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator


def test_only(
    fork: str,
) -> Callable[[StateTestSpec], Callable[[str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    fork = fork.capitalize()

    def decorator(fn: StateTestSpec) -> Callable[[str], Mapping[str, Fixture]]:
        def inner(engine) -> Mapping[str, Fixture]:
            return fill_state_test(fn, [fork], engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator
