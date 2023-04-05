"""
Decorators for expanding filler definitions.
"""
from typing import Any, Callable, List, Mapping, Optional, cast

from ethereum_test_forks import Fork, fork_only, forks_from, forks_from_until
from evm_block_builder import BlockBuilder
from evm_transition_tool import TransitionTool

from ..common import Fixture
from ..reference_spec.reference_spec import ReferenceSpec
from ..spec import TestSpec
from .fill import fill_test

TESTS_PREFIX = "test_"
TESTS_PREFIX_LEN = len(TESTS_PREFIX)

FillerReturnType = Mapping[str, Fixture] | None
DecoratedFillerType = Callable[
    [TransitionTool, BlockBuilder, str, ReferenceSpec | None], FillerReturnType
]


def _filler_decorator(
    forks: List[Fork], eips: Optional[List[int]] = None
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it for all specified forks.
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
            if not forks:
                return None
            return fill_test(
                name, t8n, b11r, fn, forks, engine, spec, eips=eips
            )

        cast(Any, inner).__filler_metadata__ = {
            "forks": forks,
            "name": name[TESTS_PREFIX_LEN:],
        }

        return inner

    return decorator


def test_from_until(
    fork_from: Fork,
    fork_until: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    return _filler_decorator(
        forks=forks_from_until(fork_from, fork_until), eips=eips
    )


def test_from(
    fork: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it for all forks after the
    specified fork.
    """
    return _filler_decorator(forks=forks_from(fork), eips=eips)


def test_only(
    fork: Fork,
    eips: Optional[List[int]] = None,
) -> Callable[[TestSpec], DecoratedFillerType]:
    """
    Decorator that takes a test generator and fills it only for the specified
    fork.
    """
    return _filler_decorator(forks=fork_only(fork), eips=eips)
