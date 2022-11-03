"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, Mapping, cast

from .fill import fill_test
from .fork import forks_from, forks_from_until
from .state_test import StateTestSpec
from .types import Fixture


def test_from_until(
    fork_from: str,
    fork_until: str,
) -> Callable[
    [StateTestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]
]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork_from = fork_from.capitalize()
    fork_until = fork_until.capitalize()

    def decorator(
        fn: StateTestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(
                t8n, b11r, fn, forks_from_until(fork_from, fork_until), engine
            )

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork_from,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator


def test_from(
    fork: str,
) -> Callable[
    [StateTestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]
]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: StateTestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(t8n, b11r, fn, forks_from(fork), engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator


def test_only(
    fork: str,
) -> Callable[
    [StateTestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]
]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: StateTestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(t8n, b11r, fn, [fork], engine)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": fn.__name__.lstrip("test_"),
        }

        return inner

    return decorator
