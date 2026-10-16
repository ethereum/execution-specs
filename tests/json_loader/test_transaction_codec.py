"""Test that decode_transaction handles legacy transactions as bytes."""

import importlib

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.exceptions import EthereumException
from ethereum.forks.amsterdam.transactions import (
    LegacyTransaction,
    decode_transaction,
)
from ethereum.state import Address


def test_decode_legacy_from_bytes() -> None:
    """Decode a legacy transaction from both bytes and object form."""
    tx = LegacyTransaction(
        nonce=U256(0),
        gas_price=Uint(1),
        gas=Uint(21000),
        to=Address(b"\x00" * 20),
        value=U256(0),
        data=Bytes(b""),
        v=U256(27),
        r=U256(1),
        s=U256(2),
    )
    encoded = rlp.encode(tx)
    assert encoded[0] >= 0xC0
    assert decode_transaction(encoded) == tx
    assert decode_transaction(tx) is tx


@pytest.mark.parametrize(
    "fork",
    [
        "berlin",
        "london",
        "arrow_glacier",
        "gray_glacier",
        "paris",
        "shanghai",
        "cancun",
        "prague",
        "osaka",
        "bpo1",
        "bpo2",
        "bpo3",
        "bpo4",
        "bpo5",
        "amsterdam",
        "bogota",
    ],
)
@pytest.mark.parametrize(
    "raw",
    [
        pytest.param(b"", id="empty"),
        pytest.param(b"\xff", id="reserved_0xff"),
        pytest.param(b"\xff\xc0", id="reserved_0xff_with_payload"),
    ],
)
def test_decode_malformed_typed_transaction(fork: str, raw: bytes) -> None:
    """
    Reject a transaction byte string with no or a reserved type byte.

    Block bodies carry typed transactions as opaque byte strings, so
    both reach `decode_transaction`. They must raise a protocol
    exception that invalidates the block, not crash the spec.
    """
    transactions = importlib.import_module(
        f"ethereum.forks.{fork}.transactions"
    )
    with pytest.raises(EthereumException):
        transactions.decode_transaction(Bytes(raw))
