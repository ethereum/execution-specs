"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, List, Mapping, Optional, Type, cast

from ethereum_test_forks import Fork, forks_from, forks_from_until

from ..common import Fixture
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import TestSpec
from .fill import fill_test

TESTS_PREFIX = "test_"
TESTS_PREFIX_LEN = len(TESTS_PREFIX)


def test_from_until(
    fork_from: Type[Fork],
    fork_until: Type[Fork],
    eips: Optional[List[int]] = None,
) -> Callable[
    [TestSpec],
    Callable[[Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]],
]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> Callable[
        [Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]
    ]:
        def inner(t8n, b11r, engine, spec) -> Mapping[str, Fixture]:
            return fill_test(
                t8n,
                b11r,
                fn,
                forks_from_until(fork_from, fork_until),
                engine,
                spec,
                eips=eips,
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
    fork: Type[Fork],
    eips: Optional[List[int]] = None,
) -> Callable[
    [TestSpec],
    Callable[[Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]],
]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> Callable[
        [Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]
    ]:
        def inner(t8n, b11r, engine, spec) -> Mapping[str, Fixture]:
            return fill_test(
                t8n, b11r, fn, forks_from(fork), engine, spec, eips=eips
            )

        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_only(
    fork: Type[Fork],
    eips: Optional[List[int]] = None,
) -> Callable[
    [TestSpec],
    Callable[[Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]],
]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> Callable[
        [Any, Any, str, ReferenceSpec | None], Mapping[str, Fixture]
    ]:
        def inner(t8n, b11r, engine, spec) -> Mapping[str, Fixture]:
            return fill_test(t8n, b11r, fn, [fork], engine, spec, eips=eips)

        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator
