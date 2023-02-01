import sys
from typing import Any

import pytest

import ethereum.london.state as state
from ethereum.base_types import U256
from ethereum.london.fork_types import EMPTY_ACCOUNT
from ethereum.london.utils.hexadecimal import hex_to_address

try:
    import ethereum_optimized.london.state_db as state_db
except ImportError:
    pass


ADDRESS_FOO = hex_to_address("0x00000000219ab540356cbb839cbe05303d7705fa")
STORAGE_FOO = U256(101).to_be_bytes32()


@pytest.mark.skipif(
    "ethereum_optimized.london.state_db" not in sys.modules,
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
    state_optimized = actions(state_db)
    assert state.get_storage(
        state_normal, ADDRESS_FOO, STORAGE_FOO
    ) == state_db.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == state_db.state_root(
        state_optimized
    )


@pytest.mark.skipif(
    "ethereum_optimized.london.state_db" not in sys.modules,
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
    state_optimized = actions(state_db)
    state_db.state_root(state_optimized)
    assert state.get_storage(
        state_normal, ADDRESS_FOO, STORAGE_FOO
    ) == state_db.get_storage(state_optimized, ADDRESS_FOO, STORAGE_FOO)
    assert state.state_root(state_normal) == state_db.state_root(
        state_optimized
    )
