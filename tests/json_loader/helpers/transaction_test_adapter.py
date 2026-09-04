"""Normalize raw transaction validation across EELS forks."""

from dataclasses import dataclass
from typing import Any

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.state import Address

from .. import FORKS


@dataclass(frozen=True)
class ValidTransactionResult:
    """Result of successfully validating a raw transaction."""

    sender: Address
    transaction_hash: Hash32
    intrinsic_gas: Uint


def _decode_transaction(transactions: Any, raw: bytes) -> Any:
    """Decode a raw transaction using the fork's transaction types."""
    legacy_transaction = getattr(transactions, "LegacyTransaction", None)
    if legacy_transaction is None:
        return rlp.decode_to(transactions.Transaction, raw)

    if raw and raw[0] < 0xC0:
        return transactions.decode_transaction(Bytes(raw))
    return rlp.decode_to(legacy_transaction, raw)


def _validate_chain_id(
    hardfork: Any,
    transactions: Any,
    transaction: Any,
    expected_chain_id: int,
) -> None:
    """Validate the chain ID when the fork supports EIP-155."""
    chain_id = getattr(transactions, "chain_id", None)
    if chain_id is None:
        return

    actual_chain_id = chain_id(transaction)
    if actual_chain_id is None:
        return

    expected = U64(expected_chain_id)
    if actual_chain_id != expected:
        exceptions = hardfork.module("exceptions")
        raise exceptions.WrongChainIdError(
            expected=expected,
            actual=actual_chain_id,
        )


def _normalize_intrinsic_gas(intrinsic_gas: Any) -> Uint:
    """Normalize scalar and split intrinsic-gas return types."""
    if hasattr(intrinsic_gas, "regular"):
        return Uint(max(intrinsic_gas.regular, intrinsic_gas.calldata_floor))
    if hasattr(intrinsic_gas, "execution"):
        return Uint(max(intrinsic_gas.execution, intrinsic_gas.calldata_floor))
    return Uint(intrinsic_gas)


def validate_raw_transaction(
    fork_name: str,
    raw: bytes,
    chain_id: int = 1,
) -> ValidTransactionResult:
    """Decode and statically validate a raw transaction for a fork."""
    hardfork = FORKS[fork_name]
    transactions = hardfork.module("transactions")

    transaction = _decode_transaction(transactions, raw)
    _validate_chain_id(hardfork, transactions, transaction, chain_id)
    sender = transactions.recover_sender(transaction)
    intrinsic_gas = transactions.validate_transaction(transaction)

    return ValidTransactionResult(
        sender=sender,
        transaction_hash=keccak256(raw),
        intrinsic_gas=_normalize_intrinsic_gas(intrinsic_gas),
    )
