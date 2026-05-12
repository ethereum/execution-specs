"""Tests for the optimized state implementation."""

from typing import Any, cast

import pytest
from ethereum_types.numeric import U256

import ethereum.state as state
from ethereum.forks.tangerine_whistle.utils.hexadecimal import hex_to_address
from ethereum.state import EMPTY_ACCOUNT
from ethereum_spec_tools.forks import Hardfork

# The optimized state integration predates the ``State`` refactor and has
# not yet been rewired onto ``PreState``/``state_tracker`` — see
# https://github.com/ethereum/execution-specs/issues/2256. Until then,
# both ``get_optimized_state_patches`` and the per-fork ``destroy_storage``
# API these tests assume no longer load, so the tests are skipped wholesale.
pytestmark = pytest.mark.skip(
    reason="optimized state pending redesign (see issue #2256)"
)

try:
    import ethereum_optimized.state_db as state_db

    class OptimizedState:
        """Placeholder for the optimized state class."""

        pass

    optimized_state = cast(Any, OptimizedState())

    frontier = Hardfork.by_short_name("frontier")
    for name, value in state_db.get_optimized_state_patches(frontier).items():
        setattr(optimized_state, name, value)

except ImportError:
    pass


ADDRESS_FOO = hex_to_address("0x00000000219ab540356cbb839cbe05303d7705fa")
STORAGE_FOO = U256(101).to_be_bytes32()


def test_storage_key() -> None:
    """
    Tests that optimized state storage operations match the normal
    implementation.
    """

    def actions(impl: Any) -> Any:
        obj = impl.State()
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        impl.set_storage(obj, ADDRESS_FOO, STORAGE_FOO, U256(42))
        impl.state_root(obj)
        return obj

    state_normal = actions(state)
    state_optimized = actions(optimized_state)
    assert state_normal.get_storage(
        ADDRESS_FOO, STORAGE_FOO
    ) == optimized_state.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == optimized_state.state_root(
        state_optimized
    )


def test_resurrection() -> None:
    """Tests that optimized state handles storage resurrection correctly."""

    def actions(impl: Any) -> Any:
        obj = impl.State()
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        impl.set_storage(obj, ADDRESS_FOO, STORAGE_FOO, U256(42))
        impl.state_root(obj)
        impl.destroy_storage(obj, ADDRESS_FOO)
        impl.state_root(obj)
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        return obj

    state_normal = actions(state)
    state_optimized = actions(optimized_state)
    optimized_state.state_root(state_optimized)
    assert state_normal.get_storage(
        ADDRESS_FOO, STORAGE_FOO
    ) == optimized_state.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == optimized_state.state_root(
        state_optimized
    )
