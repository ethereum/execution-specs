"""Test account test types."""

import copy
import pickle
from typing import Any, Callable

import ethereum.state as spec_state
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from ethereum_types.bytes import Bytes20, Bytes32
from ethereum_types.numeric import U256, Uint

from execution_testing.base_types import (
    P256_VERIFIER,
    Address,
    Hash,
    StateCommitment,
    Storage,
)

from ..account_types import Account, Alloc, P256Signer
from ..p256 import SECP256R1N
from ..transaction_types import Claim
from ..utils import keccak256

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


P256_GENERATOR = bytes.fromhex(
    "6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296"
    "4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5"
)
"""Public key `qx || qy` of the P256 private key `1`: the curve generator."""


def test_p256_signer_address() -> None:
    """The signer's address is the last 20 bytes of its public key's hash."""
    signer = P256Signer(1)
    assert signer.public_key == P256_GENERATOR
    assert signer == Address(keccak256(P256_GENERATOR)[12:])
    assert bytes(signer) == keccak256(P256_GENERATOR)[12:]


@pytest.mark.parametrize("message_byte", range(16))
def test_p256_signer_sign_message(message_byte: int) -> None:
    """
    Signatures are deterministic, low-`s`, carry the public key and verify
    against it.
    """
    signer = P256Signer(0xC0FFEE)
    message = Hash(bytes([message_byte]) * 32)
    signature = signer.sign_message(message)
    assert signature == signer.sign_message(message)
    assert len(signature) == P256Signer.signature_length
    r = int.from_bytes(signature[0:32], "big")
    s = int.from_bytes(signature[32:64], "big")
    assert 0 < r < SECP256R1N
    assert 0 < s <= SECP256R1N // 2
    assert signature[64:] == signer.public_key
    public_key = ec.EllipticCurvePublicNumbers(
        int.from_bytes(signature[64:96], "big"),
        int.from_bytes(signature[96:128], "big"),
        ec.SECP256R1(),
    ).public_key()
    public_key.verify(
        utils.encode_dss_signature(r, s),
        bytes(message),
        ec.ECDSA(utils.Prehashed(hashes.SHA256())),
    )


def test_p256_signer_claim() -> None:
    """A P256 signer builds a `P256_VERIFIER` claim keyed by its address."""
    signer = P256Signer(1)
    claim = Claim(signer=signer)
    assert claim.verifier == P256_VERIFIER
    assert claim.key == bytes(signer)
    assert claim.signed_by is signer


@pytest.mark.parametrize(
    "duplicate",
    [
        pytest.param(copy.copy, id="copy"),
        pytest.param(copy.deepcopy, id="deepcopy"),
        pytest.param(
            lambda signer: pickle.loads(pickle.dumps(signer)), id="pickle"
        ),
    ],
)
def test_p256_signer_duplicates(duplicate: Callable[[Any], Any]) -> None:
    """
    A copied or unpickled P256 signer keeps its address, key, public key
    and label, and signs like the original.
    """
    signer = P256Signer(0xC0FFEE, label="p256_signer")
    duplicated = duplicate(signer)
    assert isinstance(duplicated, P256Signer)
    assert bytes(duplicated) == bytes(signer)
    assert duplicated.key == signer.key
    assert duplicated.public_key == signer.public_key
    assert duplicated.label == signer.label
    message = Hash(b"\x42" * 32)
    assert duplicated.sign_message(message) == signer.sign_message(message)
