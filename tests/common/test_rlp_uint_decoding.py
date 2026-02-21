"""Tests for RLP decoding behavior for Uint values."""

import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import Uint


@pytest.mark.parametrize("encoded_uint", [b"\x00", b"\x82\x00\x01"])
def test_decode_to_uint_rejects_leading_zero_bytes(
    encoded_uint: bytes,
) -> None:
    """Uint decoding should reject non-canonical leading-zero encodings."""
    with pytest.raises(rlp.DecodingError):
        rlp.decode_to(Uint, encoded_uint)
