"""Test that decode_transaction handles transactions given as bytes."""

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.forks.amsterdam.transactions import (
    LegacyTransaction,
    decode_transaction,
)
from ethereum.forks.amsterdam.transactions.frame_transaction import (
    FrameTransaction,
    TransactionFees,
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


def frame_transaction(chain_id: U256) -> FrameTransaction:
    """Build a frame transaction carrying the given chain id."""
    return FrameTransaction(
        chain_id=chain_id,
        nonce=U256(0),
        sender=Address(b"\x00" * 20),
        frames=(),
        signatures=(),
        fees=TransactionFees(
            max_priority_fee_per_gas=Uint(0),
            max_fee_per_gas=Uint(0),
            max_fee_per_blob_gas=U256(0),
        ),
        blob_versioned_hashes=(),
    )


@pytest.mark.parametrize("chain_id", [U256(1), U256(2**64), U256(2**256 - 1)])
def test_decode_frame_chain_id_is_256_bits(chain_id: U256) -> None:
    """
    Decode a frame transaction whose chain id needs more than the 64
    bits every other transaction type allows.

    [EIP-8141] bounds the field at `2**256`, so a wide chain id decodes
    and is rejected later for naming another chain, rather than failing
    to decode at all.

    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """
    tx = frame_transaction(chain_id)
    encoded = Bytes(b"\x06" + rlp.encode(tx))

    assert decode_transaction(encoded) == tx
