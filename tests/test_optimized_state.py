import sys
from typing import Any, cast

import pytest

import ethereum.frontier.state as state
from ethereum.base_types import U256
from ethereum.frontier.fork_types import EMPTY_ACCOUNT
from ethereum.tangerine_whistle.utils.hexadecimal import hex_to_address

try:
    import ethereum_optimized.state_db as state_db

    class OptimizedState:
        pass

    optimized_state = cast(Any, OptimizedState())

    for (name, value) in state_db.get_optimized_state_patches(
        "frontier"
    ).items():
        setattr(optimized_state, name, value)

except ImportError:
    pass


ADDRESS_FOO = hex_to_address("0x00000000219ab540356cbb839cbe05303d7705fa")
STORAGE_FOO = U256(101).to_be_bytes32()


@pytest.mark.skipif(
    "ethereum_optimized.state_db" not in sys.modules,
    reason="missing dependency (use `pip install 'ethereum[optimized]'`)",
)
def test_storage_key() -> None:
    def actions(impl: Any) -> Any:
        obj = impl.State()
        impl.set_account(obj, ADDRESS_FOO, EMPTY_ACCOUNT)
        impl.set_storage(obj, ADDRESS_FOO, STORAGE_FOO, U256(42))
        impl.state_root(obj)
        return obj

    state_normal = actions(state)
    state_optimized = actions(optimized_state)
    assert state.get_storage(
        state_normal, ADDRESS_FOO, STORAGE_FOO
    ) == optimized_state.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == optimized_state.state_root(
        state_optimized
    )


@pytest.mark.skipif(
    "ethereum_optimized.state_db" not in sys.modules,
    reason="missing dependency (use `pip install 'ethereum[optimized]'`)",
)
def test_resurrection() -> None:
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
    assert state.get_storage(
        state_normal, ADDRESS_FOO, STORAGE_FOO
    ) == optimized_state.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == optimized_state.state_root(
        state_optimized
    )
