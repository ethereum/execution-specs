"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, List, Mapping, Optional, cast

from ethereum_test_forks import Fork, forks_from, forks_from_until
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import Fixture
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import TestSpec
from .fill import fill_test

TESTS_PREFIX = "test_"
TESTS_PREFIX_LEN = len(TESTS_PREFIX)

FillerReturnType = Mapping[str, Fixture]
DecoratedFillerType = Callable[
    [TransitionTool, BlockBuilder, str, ReferenceSpec | None], FillerReturnType
]


def test_from_until(
    fork_from: Fork,
    fork_until: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> DecoratedFillerType:
        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        def inner(
            t8n: TransitionTool,
            b11r: BlockBuilder,
            engine: str,
            spec: ReferenceSpec | None,
        ) -> FillerReturnType:
            return fill_test(
                name,
                t8n,
                b11r,
                fn,
                forks_from_until(fork_from, fork_until),
                engine,
                spec,
                eips=eips,
            )

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork_from,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_from(
    fork: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> DecoratedFillerType:
        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        def inner(
            t8n: TransitionTool,
            b11r: BlockBuilder,
            engine: str,
            spec: ReferenceSpec | None,
        ) -> FillerReturnType:
            return fill_test(
                name, t8n, b11r, fn, forks_from(fork), engine, spec, eips=eips
            )

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_only(
    fork: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """

    def decorator(
        fn: TestSpec,
    ) -> DecoratedFillerType:
        name = fn.__name__
        assert name.startswith(TESTS_PREFIX)

        def inner(
            t8n: TransitionTool,
            b11r: BlockBuilder,
            engine: str,
            spec: ReferenceSpec | None,
        ) -> FillerReturnType:
            return fill_test(
                name, t8n, b11r, fn, [fork], engine, spec, eips=eips
            )

        cast(Any, inner).__filler_metadata__ = {
            "fork": fork,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator
