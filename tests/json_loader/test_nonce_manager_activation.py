"""
Exercise the EIP-8250 install on the spec's own state.

Fixtures cover the occupied address through the filler's state. These
cases pin the spec state's storage query and the cleared-storage case,
which no fixture can reach.
"""

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.forks.bogota.fork import install_nonce_manager
from ethereum.forks.bogota.state_tracker import (
    BlockState,
    TransactionState,
    get_account,
)
from ethereum.forks.bogota.transactions.frame_transaction import (
    NONCE_MANAGER,
    NONCE_MANAGER_CODE,
)
from ethereum.state import EMPTY_CODE_HASH, Account
from ethereum.state_mpt import State, set_account, set_storage, store_code

SLOT = Bytes32(b"\x11" * 32)
"""Storage slot written at the nonce manager address."""


@pytest.mark.parametrize(
    "code,storage,reason",
    [
        pytest.param(
            NONCE_MANAGER_CODE, False, "code", id="nonce_manager_code"
        ),
        pytest.param(Bytes(b"\x00"), False, "code", id="foreign_code"),
        pytest.param(None, True, "storage", id="storage_without_code"),
        pytest.param(
            Bytes(b"\x00"), True, "code", id="foreign_code_and_storage"
        ),
    ],
)
def test_install_rejects_occupied_address(
    code: Bytes | None, storage: bool, reason: str
) -> None:
    """Reject code or storage at the address before writing anything."""
    state = State()
    code_hash = EMPTY_CODE_HASH if code is None else store_code(state, code)
    set_account(state, NONCE_MANAGER, Account(Uint(7), U256(42), code_hash))
    if storage:
        set_storage(state, NONCE_MANAGER, SLOT, U256(1))
    assert state.account_has_storage(NONCE_MANAGER) == storage

    tx_state = TransactionState(parent=BlockState(pre_state=state))
    with pytest.raises(InvalidBlock, match=f"already holds {reason}"):
        install_nonce_manager(tx_state)
    assert tx_state.account_writes == {}
    assert tx_state.code_writes == {}


def test_install_after_storage_cleared() -> None:
    """
    Install over an account whose only storage slot was cleared. No
    fixture reaches this: before the fork nothing can write storage at
    the address, which runs no code and has no known key.
    """
    state = State()
    set_account(
        state, NONCE_MANAGER, Account(Uint(7), U256(42), EMPTY_CODE_HASH)
    )
    set_storage(state, NONCE_MANAGER, SLOT, U256(1))
    set_storage(state, NONCE_MANAGER, SLOT, U256(0))
    assert not state.account_has_storage(NONCE_MANAGER)

    tx_state = TransactionState(parent=BlockState(pre_state=state))
    install_nonce_manager(tx_state)

    assert get_account(tx_state, NONCE_MANAGER) == Account(
        Uint(7), U256(42), keccak256(NONCE_MANAGER_CODE)
    )
