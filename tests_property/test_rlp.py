"""
Properties of how the spec RLP-encodes and decodes its transactions.

Transactions are compared with the framework's own encoding of the same
transaction, which is written apart from `src/`.
"""

from types import ModuleType
from typing import Any, List

import pytest
from ethereum_types.bytes import Bytes
from execution_testing import TransactionType
from execution_testing.forks import Fork
from hypothesis import given
from hypothesis import strategies as st

from ethereum.exceptions import InvalidBlock
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import (
    decode_transaction,
    encode_transaction,
    spec_transaction,
    transaction_types,
    type_byte,
)
from .strategies import aim_at, framework_txs

# Yellow Paper, Appendix B: a string this long or longer takes a long
# length prefix. Every signed transaction is already a long list.
LONG_STRING = 56
# EIP-2718: a first byte up to this one is a transaction type, not RLP.
LAST_TYPE_BYTE = 0x7F

with_typed_transactions = requires(lambda fork: max(fork.tx_types()) > 0)
# EIP-2718: a first byte past the type range starts an RLP string or 0xff,
# and starts neither a typed transaction nor a legacy one, an RLP list.
NEITHER_FIRST_BYTES = [*range(LAST_TYPE_BYTE + 1, 0xC0), 0xFF]


def test_transaction_types_match_the_framework(
    fork: Fork, transactions: ModuleType
) -> None:
    """The spec defines exactly the transaction types the framework lists."""
    spec_type_bytes = [
        type_byte(tx_type) for tx_type in transaction_types(transactions)
    ]
    assert sorted(spec_type_bytes) == sorted(fork.tx_types())


def has_type(ty: int) -> pytest.MarkDecorator:
    """Return a mark that runs a test only on forks with type `ty`."""
    return requires(lambda fork: ty in fork.tx_types())


def each_transaction_type() -> List[Any]:
    """Return every transaction type as a parameter for forks that have it."""
    return [
        pytest.param(ty, id=ty.name.lower(), marks=has_type(ty))
        for ty in TransactionType
    ]


@pytest.mark.parametrize("tx_type", each_transaction_type())
@given(data=st.data())
def test_transaction_encoding_matches_the_framework(
    fork: Fork, transactions: ModuleType, data: st.DataObject, tx_type: int
) -> None:
    """
    Every transaction type encodes to the framework's encoding of the same
    transaction, and decodes back to itself.
    """
    framework = data.draw(framework_txs(fork, [tx_type]))
    aim_at(len(framework.data), LONG_STRING, "calldata near a long prefix")
    tx = spec_transaction(transactions, framework)
    assert encode_transaction(transactions, tx) == framework.rlp()
    assert decode_transaction(transactions, framework.rlp()) == tx


@with_typed_transactions
@given(data=st.data(), payload=st.binary(max_size=8))
def test_decoding_rejects_unknown_types(
    fork: Fork,
    spec: Hardfork,
    transactions: ModuleType,
    data: st.DataObject,
    payload: bytes,
) -> None:
    """
    An encoding that starts with a byte in the transaction type range,
    but not one of the fork's types, is rejected.
    """
    unknown_types = [
        byte
        for byte in range(LAST_TYPE_BYTE + 1)
        if byte == 0 or byte not in fork.tx_types()
    ]
    unknown = data.draw(st.sampled_from(unknown_types))
    aim_at(unknown, max(fork.tx_types()) + 1, "type byte near the newest")

    with pytest.raises(spec.module("exceptions").TransactionTypeError):
        transactions.decode_transaction(Bytes([unknown]) + payload)


@with_typed_transactions
def test_decoding_rejects_an_empty_encoding(transactions: ModuleType) -> None:
    """An empty encoding is no transaction."""
    with pytest.raises(InvalidBlock):
        transactions.decode_transaction(Bytes(b""))


@with_typed_transactions
@given(
    first=st.one_of(
        st.sampled_from([0x80, 0xBF, 0xFF]),
        st.sampled_from(NEITHER_FIRST_BYTES),
    ),
    payload=st.binary(max_size=8),
)
def test_decoding_rejects_bytes_that_start_neither_kind(
    spec: Hardfork, transactions: ModuleType, first: int, payload: bytes
) -> None:
    """
    An encoding whose first byte starts neither a transaction type nor an
    RLP list is rejected on every fork with typed transactions.
    """
    with pytest.raises(spec.module("exceptions").TransactionTypeError):
        transactions.decode_transaction(Bytes([first]) + payload)
