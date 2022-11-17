"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, Mapping, cast

from ..common import Fixture
from ..spec import TestSpec
from ..vm.fork import forks_from, forks_from_until
from .fill import fill_test

TESTS_PREFIX = "test_"
TESTS_PREFIX_LEN = len(TESTS_PREFIX)


def test_from_until(
    fork_from: str,
    fork_until: str,
) -> Callable[[TestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork_from = fork_from.capitalize()
    fork_until = fork_until.capitalize()

    def decorator(
        fn: TestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(
                t8n, b11r, fn, forks_from_until(fork_from, fork_until), engine
            )

        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork_from,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_from(
    fork: str,
) -> Callable[[TestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: TestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(t8n, b11r, fn, forks_from(fork), engine)

        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_only(
    fork: str,
) -> Callable[[TestSpec], Callable[[Any, Any, str], Mapping[str, Fixture]]]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    fork = fork.capitalize()

    def decorator(
        fn: TestSpec,
    ) -> Callable[[Any, Any, str], Mapping[str, Fixture]]:
        def inner(t8n, b11r, engine) -> Mapping[str, Fixture]:
            return fill_test(t8n, b11r, fn, [fork], engine)

        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator
