"""Test that decode_transaction handles legacy transactions as bytes."""

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

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
