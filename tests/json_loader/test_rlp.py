"""
Test that RLP decoding rejects non-canonical integer encodings.

RLP encodes integers big-endian without leading zero bytes; zero is
the empty byte string, not `0x00`. Execution clients enforce this, so
the `ethereum-rlp` dependency must too.
"""

from typing import Union

import pytest
from ethereum_rlp import rlp
from ethereum_rlp.exceptions import DecodingError
from ethereum_types.numeric import U64, U256, Uint


@pytest.mark.parametrize(
    "encoded, expected",
    [
        pytest.param(b"\x80", 0, id="zero-empty-string"),
        pytest.param(b"\x01", 1, id="one"),
        pytest.param(b"\x7f", 0x7F, id="single-byte-max"),
        pytest.param(b"\x81\x80", 0x80, id="smallest-prefixed"),
        pytest.param(b"\x82\x01\x00", 0x0100, id="two-bytes"),
    ],
)
def test_decode_to_uint_accepts_canonical(
    encoded: bytes, expected: int
) -> None:
    """Decode canonical integer encodings to the expected value."""
    assert rlp.decode_to(Uint, encoded) == Uint(expected)


@pytest.mark.parametrize(
    "integer_type", [Uint, U64, U256], ids=["Uint", "U64", "U256"]
)
@pytest.mark.parametrize(
    "encoded",
    [
        pytest.param(b"\x00", id="single-zero-byte"),
        pytest.param(b"\x82\x00\x01", id="leading-zero-two-bytes"),
        pytest.param(b"\x83\x00\x00\x01", id="leading-zeros-three-bytes"),
    ],
)
def test_decode_to_integer_rejects_leading_zeros(
    integer_type: type[Union[Uint, U64, U256]], encoded: bytes
) -> None:
    """Reject integer encodings with leading zero bytes."""
    with pytest.raises(DecodingError, match="non-canonical"):
        rlp.decode_to(integer_type, encoded)
