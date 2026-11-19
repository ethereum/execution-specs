"""
Build spec objects and call spec functions the same way on every fork.

Each fork is a full copy of the one before, so names and signatures drift
between them. This module is the one place that knows how they differ, and
the one bridge from the framework's transactions to the spec's.
"""

import dataclasses
import inspect
from types import ModuleType, SimpleNamespace, UnionType
from typing import (
    Any,
    Optional,
    Set,
    Tuple,
    Union,
    get_args,
    get_origin,
)

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes0
from ethereum_types.numeric import FixedUnsigned, Uint
from execution_testing import Transaction, TransactionType

from ethereum.state import Address

# The spec's class for each EIP-2718 transaction type. Forks before typed
# transactions name their only class `Transaction`.
TYPE_BYTES = {
    "Transaction": TransactionType.LEGACY,
    "LegacyTransaction": TransactionType.LEGACY,
    "AccessListTransaction": TransactionType.ACCESS_LIST,
    "FeeMarketTransaction": TransactionType.BASE_FEE,
    "BlobTransaction": TransactionType.BLOB_TRANSACTION,
    "SetCodeTransaction": TransactionType.SET_CODE,
}

# Spec field names that the framework spells differently.
FRAMEWORK_FIELD_NAMES = {
    "gas": "gas_limit",
    "y_parity": "v",
    "authorizations": "authorization_list",
    "account": "address",
    "slots": "storage_keys",
}


def _zero_value(field_type: Any) -> Any:
    origin = get_origin(field_type)
    if origin in (UnionType, Union):
        options = get_args(field_type)
        if type(None) in options:
            return None
        field_type = options[0]
        origin = get_origin(field_type)
    if origin in (tuple, list, set, dict):
        return origin()
    if isinstance(field_type, type) and issubclass(field_type, bool):
        return False
    if isinstance(field_type, type) and issubclass(
        field_type, (FixedUnsigned, Uint)
    ):
        return field_type(0)
    length = getattr(field_type, "LENGTH", None)
    if length is not None:
        return field_type(b"\x00" * length)
    return field_type(b"")


def zeroed(cls: Any, **overrides: Any) -> Any:
    """Build a dataclass with every field zero or empty except `overrides`."""
    fields = {
        f.name: overrides[f.name]
        if f.name in overrides
        else _zero_value(f.type)
        for f in dataclasses.fields(cls)
    }
    return cls(**fields)


def transaction_types(transactions: ModuleType) -> Tuple[type, ...]:
    """Return every transaction class of a fork."""
    return get_args(transactions.Transaction) or (transactions.Transaction,)


def type_byte(tx_type: type) -> int:
    """Return the EIP-2718 type byte of a transaction class."""
    return TYPE_BYTES[tx_type.__name__]


def _spec_value(field_type: Any, value: Any) -> Any:
    origin = get_origin(field_type)
    if origin is tuple:
        item_type, _ = get_args(field_type)
        return tuple(_spec_value(item_type, item) for item in value or ())
    if origin in (UnionType, Union):
        # Only `to` is a union: empty for a contract creation.
        return Bytes0(b"") if value is None else Address(value)
    if dataclasses.is_dataclass(field_type):
        return _spec_object(field_type, value)
    if issubclass(field_type, (FixedUnsigned, Uint)):
        return field_type(int(value))
    return field_type(bytes(value))


def _spec_object(cls: Any, framework_object: Any) -> Any:
    return cls(
        **{
            field.name: _spec_value(
                field.type,
                getattr(
                    framework_object,
                    FRAMEWORK_FIELD_NAMES.get(field.name, field.name),
                ),
            )
            for field in dataclasses.fields(cls)
        }
    )


def spec_transaction(transactions: ModuleType, tx: Transaction) -> Any:
    """Return the spec's copy of a framework transaction."""
    (tx_type,) = (
        tx_type
        for tx_type in transaction_types(transactions)
        if type_byte(tx_type) == tx.ty
    )
    return _spec_object(tx_type, tx)


def spec_authorization(fork_types: ModuleType, authorization: Any) -> Any:
    """Return the spec's copy of a framework EIP-7702 authorization."""
    return _spec_object(fork_types.Authorization, authorization)


def validate_authorization(
    vm: ModuleType, block_env: Any, tx_env: Any, authorization: Any
) -> Tuple[Optional[Address], Set[Address]]:
    """
    Check one EIP-7702 authorization, and return its authority, or None if
    it is invalid, with the addresses the check warmed.

    Some forks warm the authority in the message's accessed addresses, and
    later ones collect it in a set of its own.
    """
    validate = vm.eoa_delegation.validate_authorization
    accessed: Set[Address] = set()
    if "message" not in inspect.signature(validate).parameters:
        return validate(block_env, tx_env, accessed, authorization), accessed
    message = zeroed(
        vm.Message,
        block_env=block_env,
        tx_env=tx_env,
        accessed_addresses=accessed,
    )
    return validate(message, authorization), accessed


def encode_transaction(transactions: ModuleType, tx: Any) -> bytes:
    """Return a transaction's encoding, with its type byte if it has one."""
    encode = getattr(transactions, "encode_transaction", None)
    encoded = tx if encode is None else encode(tx)
    return encoded if isinstance(encoded, bytes) else rlp.encode(encoded)


def decode_transaction(transactions: ModuleType, encoded: bytes) -> Any:
    """Decode a transaction encoded by `encode_transaction`."""
    if not hasattr(transactions, "decode_transaction"):
        return rlp.decode_to(transactions.Transaction, encoded)
    if encoded[0] >= 0xC0:
        # An RLP list: a legacy transaction.
        return rlp.decode_to(transactions.LegacyTransaction, encoded)
    return transactions.decode_transaction(encoded)


def sender_of(transactions: ModuleType, tx: Any) -> Address:
    """
    Recover a transaction's sender, after the EIP-155 chain id check that
    forks with one run first.
    """
    if hasattr(transactions, "chain_id"):
        transactions.chain_id(tx)
    return transactions.recover_sender(tx)


def validate_tx(transactions: ModuleType, tx: Any, sender: bytes) -> None:
    """Validate `tx` as sent by `sender`, on forks that take a sender."""
    validate = transactions.validate_transaction
    if "sender" in inspect.signature(validate).parameters:
        validate(tx, Address(sender))
    else:
        validate(tx)


def validate_header(fork: ModuleType, parent: Any, header: Any) -> None:
    """
    Validate `header` against `parent`, on forks that read the parent from
    the chain as well as on those that take it directly.
    """
    validate = fork.validate_header
    if "chain" in inspect.signature(validate).parameters:
        chain = SimpleNamespace(blocks=[SimpleNamespace(header=parent)])
        validate(chain, header)
    else:
        validate(parent, header)


def modify_deletes_empty_accounts(tracker: ModuleType) -> bool:
    """
    Return whether a change that leaves an account empty deletes it.

    Forks that sweep touched empty accounts at the end of a transaction
    keep them until then; later forks delete them on the spot. The answer
    is read from the spec's own tracker, which only `spec_unit` tests may
    do.
    """
    return not hasattr(tracker, "destroy_touched_empty_accounts")
