"""Test account test types."""

from typing import Callable

import ethereum.state as spec_state
import pytest
from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import Address, StateCommitment, Storage

from ..account_types import Account, Alloc

STORAGE_WRITES: dict[str, Callable[[Storage], object]] = {
    "setitem": lambda storage: storage.__setitem__(1, 2),
    "delitem": lambda storage: storage.__delitem__(0),
    "store_next": lambda storage: storage.store_next(2),
    "set_next_slot": lambda storage: storage.set_next_slot(5),
    "set_expect_any": lambda storage: storage.set_expect_any(0),
}
"""Every way of writing to a `Storage`, each applied to one with slot 0."""


@pytest.mark.parametrize(
    "account_1, account_2, equal",
    [
        (Account(), Account(), True),
        (Account(nonce=1), Account(nonce=2), False),
        (Account(nonce=1), Account(nonce=1), True),
        (Account(nonce=1), Account(nonce=1, code="0x1234"), False),
        (Account(nonce=1, code="0x1234"), Account(nonce=1), False),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x1234"),
            True,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x5678"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=2, code="0x5678"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=2, code="0x1234"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x1234", storage={0: 0, 1: 1}),
            False,
        ),
        (
            Account(nonce=1, code="0x1234", storage={1: 1, 0: 0}),
            Account(nonce=1, code="0x1234", storage={0: 0, 1: 1}),
            True,
        ),
    ],
)
def test_account_hash(
    account_1: Account, account_2: Account, equal: bool
) -> None:
    """Test two different accounts to return the same hash."""
    if equal:
        assert account_1.hash() == account_2.hash(), (
            f"Account 1: {account_1.hash()}, Account 2: {account_2.hash()}"
        )
    else:
        assert account_1.hash() != account_2.hash(), (
            f"Account 1: {account_1.hash()}, Account 2: {account_2.hash()}"
        )


@pytest.mark.parametrize("write", STORAGE_WRITES.values(), ids=STORAGE_WRITES)
def test_storage_outside_account_is_writable(
    write: Callable[[Storage], object],
) -> None:
    """Allow every write to a storage no account holds."""
    write(Storage({0: 1}))


@pytest.mark.parametrize("write", STORAGE_WRITES.values(), ids=STORAGE_WRITES)
def test_storage_frozen_by_account(write: Callable[[Storage], object]) -> None:
    """
    Reject every write to a storage once an account holds it, including
    through the caller's reference.
    """
    storage = Storage({0: 1})
    account = Account(storage=storage)
    assert account.storage is storage
    with pytest.raises(TypeError, match="Storage is frozen"):
        write(storage)
    assert storage == Storage({0: 1})


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(Account(), id="default_storage"),
        pytest.param(Account(storage={0: 1}), id="dict_storage"),
        pytest.param(
            Account.model_validate({"storage": {"0x00": "0x01"}}),
            id="validated_storage",
        ),
    ],
)
def test_account_storage_is_frozen(account: Account) -> None:
    """Freeze the storage however the account was created."""
    with pytest.raises(TypeError, match="Storage is frozen"):
        account.storage[1] = 2


def test_apply_diff_storages_are_frozen() -> None:
    """
    Freeze the storages `apply_diff` swaps in, which skip the account's
    validation.
    """
    changed, cleared, zeroed = Address(0x1), Address(0x2), Address(0x3)
    alloc = Alloc(
        {
            changed: Account(storage={0: 1}),
            cleared: Account(storage={0: 1}),
            zeroed: Account(storage={0: 0, 1: 1}),
        }
    )
    alloc.migrate_state_commitment(StateCommitment.MPT)
    alloc.get_account_optional(Bytes20(changed))
    diff = spec_state.BlockDiff(
        account_changes={
            Bytes20(cleared): spec_state.Account(
                nonce=Uint(0),
                balance=U256(0),
                code_hash=spec_state.EMPTY_CODE_HASH,
            )
        },
        storage_changes={
            Bytes20(changed): {Bytes32(b"\x00" * 31 + b"\x01"): U256(2)},
        },
        storage_clears={Bytes20(cleared)},
    )
    alloc.apply_diff(diff)

    for address in (changed, cleared, zeroed):
        account = alloc[address]
        assert account is not None
        with pytest.raises(TypeError, match="Storage is frozen"):
            account.storage[5] = 5
    assert alloc[changed] == Account(storage={0: 1, 1: 2})
    assert alloc[cleared] == Account()
    assert alloc[zeroed] == Account(storage={1: 1})
