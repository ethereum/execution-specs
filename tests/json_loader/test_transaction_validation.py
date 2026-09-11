"""Test state-independent transaction validation across EELS forks."""

from importlib import import_module
from typing import Any

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import Transaction as FixtureTransaction

from ethereum.crypto.hash import Hash32
from ethereum.state import Address

BLOB_FORKS = (
    "cancun",
    "prague",
    "osaka",
    "bpo1",
    "bpo2",
    "bpo3",
    "bpo4",
    "bpo5",
    "amsterdam",
)
SET_CODE_FORKS = BLOB_FORKS[1:]
BLOB_COUNT_FORKS = BLOB_FORKS[2:]

SENDER = Address(b"\x11" * 20)
RECIPIENT = Address(b"\x22" * 20)
VALID_BLOB_HASH = Hash32(b"\x01" + b"\x00" * 31)
INVALID_BLOB_HASH = Hash32(b"\x02" + b"\x00" * 31)


def _modules(fork_name: str) -> tuple[Any, Any]:
    """Load a fork's transaction and exception modules."""
    prefix = f"ethereum.forks.{fork_name}"
    return (
        import_module(f"{prefix}.transactions"),
        import_module(f"{prefix}.exceptions"),
    )


def _blob_transaction(
    transactions: Any,
    *,
    to: Address | Bytes0 = RECIPIENT,
    blob_hashes: tuple[Hash32, ...] = (VALID_BLOB_HASH,),
) -> Any:
    """Build a blob transaction for direct validation."""
    return transactions.BlobTransaction(
        chain_id=U64(1),
        nonce=U256(0),
        max_priority_fee_per_gas=Uint(1),
        max_fee_per_gas=Uint(1),
        gas=Uint(100_000),
        to=to,
        value=U256(0),
        data=Bytes(b""),
        access_list=(),
        max_fee_per_blob_gas=U256(1),
        blob_versioned_hashes=blob_hashes,
        y_parity=U256(0),
        r=U256(1),
        s=U256(1),
    )


def _set_code_transaction(
    transactions: Any,
    *,
    to: Address | Bytes0 = RECIPIENT,
) -> Any:
    """Build a set-code transaction for direct validation."""
    return transactions.SetCodeTransaction(
        chain_id=U64(1),
        nonce=U64(0),
        max_priority_fee_per_gas=Uint(1),
        max_fee_per_gas=Uint(1),
        gas=Uint(100_000),
        to=to,
        value=U256(0),
        data=Bytes(b""),
        access_list=(),
        authorizations=(),
        y_parity=U256(0),
        r=U256(1),
        s=U256(1),
    )


def _validate(fork_name: str, transactions: Any, tx: Any) -> None:
    """Validate a transaction while avoiding signature recovery in fixtures."""
    if fork_name == "amsterdam":
        transactions.validate_transaction(tx, SENDER)
    else:
        transactions.validate_transaction(tx)


@pytest.mark.parametrize("fork_name", BLOB_FORKS)
def test_blob_transaction_requires_data(fork_name: str) -> None:
    """Reject a blob transaction without versioned hashes."""
    transactions, exceptions = _modules(fork_name)
    tx = _blob_transaction(transactions, blob_hashes=())

    with pytest.raises(exceptions.NoBlobDataError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", BLOB_FORKS)
def test_blob_transaction_requires_supported_hash_version(
    fork_name: str,
) -> None:
    """Reject a blob transaction with an unsupported hash version."""
    transactions, exceptions = _modules(fork_name)
    tx = _blob_transaction(transactions, blob_hashes=(INVALID_BLOB_HASH,))

    with pytest.raises(exceptions.InvalidBlobVersionedHashError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", BLOB_FORKS)
def test_blob_transaction_cannot_create_contract(fork_name: str) -> None:
    """Reject contract creation by a blob transaction."""
    transactions, exceptions = _modules(fork_name)
    tx = _blob_transaction(transactions, to=Bytes0(b""))

    with pytest.raises(exceptions.TransactionTypeContractCreationError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", BLOB_COUNT_FORKS)
def test_blob_transaction_count_is_limited(fork_name: str) -> None:
    """Reject a blob transaction that exceeds the per-transaction limit."""
    transactions, exceptions = _modules(fork_name)
    tx = _blob_transaction(
        transactions,
        blob_hashes=(VALID_BLOB_HASH,) * 7,
    )

    with pytest.raises(exceptions.BlobCountExceededError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", SET_CODE_FORKS)
def test_set_code_transaction_requires_authorization(fork_name: str) -> None:
    """Reject a set-code transaction without authorizations."""
    transactions, exceptions = _modules(fork_name)
    tx = _set_code_transaction(transactions)

    with pytest.raises(exceptions.EmptyAuthorizationListError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", SET_CODE_FORKS)
def test_set_code_transaction_cannot_create_contract(fork_name: str) -> None:
    """Reject contract creation by a set-code transaction."""
    transactions, exceptions = _modules(fork_name)
    tx = _set_code_transaction(transactions, to=Bytes0(b""))

    with pytest.raises(exceptions.TransactionTypeContractCreationError):
        _validate(fork_name, transactions, tx)


@pytest.mark.parametrize("fork_name", BLOB_FORKS[:-1])
def test_validation_accepts_legacy_transaction(fork_name: str) -> None:
    """Accept a valid legacy transaction through the public validator."""
    transactions, _ = _modules(fork_name)
    raw = Bytes(
        FixtureTransaction(gas_limit=100_000).with_signature_and_sender().rlp()
    )
    tx = rlp.decode_to(transactions.LegacyTransaction, raw)

    transactions.validate_transaction(tx)


def test_amsterdam_validation_can_recover_sender() -> None:
    """Validate an Amsterdam transaction without precomputing its sender."""
    transactions, _ = _modules("amsterdam")
    raw = Bytes(
        FixtureTransaction(gas_limit=100_000).with_signature_and_sender().rlp()
    )
    tx = transactions.decode_transaction(raw)
    sender = transactions.recover_sender(tx)

    assert transactions.validate_transaction(tx) == (
        transactions.validate_transaction(tx, sender)
    )
