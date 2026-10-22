"""Test account test types."""

from typing import Callable

import ethereum.state as spec_state
import pytest
from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import (
    Address,
    StateCommitment,
    Storage,
    TestPrivateKey,
)

from ..account_types import EOA, Account, Alloc

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
    write(Storage({0: 1}))  # type: ignore[dict-item]


@pytest.mark.parametrize("write", STORAGE_WRITES.values(), ids=STORAGE_WRITES)
def test_storage_frozen_by_account(write: Callable[[Storage], object]) -> None:
    """
    Reject every write to a storage once an account holds it, including
    through the caller's reference.
    """
    storage = Storage({0: 1})  # type: ignore[dict-item]
    account = Account(storage=storage)
    assert account.storage is storage
    with pytest.raises(TypeError, match="Storage is frozen"):
        write(storage)
    assert storage == Storage({0: 1})  # type: ignore[dict-item]


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


def test_update_account_keeps_other_fields() -> None:
    """Replace only the fields given, keeping the rest of the account."""
    alloc = Alloc(
        {
            Address(0x1000): Account(
                nonce=1, balance=2, code="0x00", storage={0: 1}
            )
        }
    )
    alloc.update_account(0x1000, code="0x5f", storage={1: 2})
    assert alloc[0x1000] == Account(
        nonce=1, balance=2, code="0x5f", storage={1: 2}
    )


def test_update_account_requires_account() -> None:
    """Refuse to update an account the allocation does not hold."""
    with pytest.raises(ValueError, match="No account"):
        Alloc().update_account(0x1000, code="0x5f")


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


@pytest.mark.parametrize(
    "digest",
    [
        pytest.param(b"\x00" * 32, id="zero"),
        pytest.param(keccak256(b"ecrecover"), id="keccak"),
        pytest.param(b"\xff" * 32, id="max"),
    ],
)
def test_eoa_sign_digest_recovers_signer(digest: bytes) -> None:
    """
    Test that the spec's recovery maps a digest signature back to the
    signer, with a low `s` and `v` in the form ecrecover takes.
    """
    eoa = EOA(key=TestPrivateKey)
    v, r, s = eoa.sign_digest(digest)
    assert v in (27, 28)
    assert 0 < s <= int(SECP256K1N) // 2
    public_key = secp256k1_recover(
        U256(r), U256(s), U256(v - 27), Hash32(digest)
    )
    assert Address(keccak256(public_key)[12:32]) == eoa


def test_eoa_sign_digest_requires_key() -> None:
    """Test that an EOA known only by its address cannot sign."""
    eoa = EOA(Address(0x1234))
    with pytest.raises(ValueError, match="private key"):
        eoa.sign_digest(b"\x00" * 32)


@pytest.mark.parametrize(
    "digest",
    [
        pytest.param(b"\x01" * 31, id="short"),
        pytest.param(b"\x01" * 33, id="long"),
    ],
)
def test_eoa_sign_digest_requires_32_bytes(digest: bytes) -> None:
    """Test that a digest of any other length is rejected, not padded."""
    eoa = EOA(key=TestPrivateKey)
    with pytest.raises(ValueError, match="fixed size bytes"):
        eoa.sign_digest(digest)
