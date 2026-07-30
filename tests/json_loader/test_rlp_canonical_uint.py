"""
Test that decoding RLP into integer types rejects non-canonical
integers.

Canonical RLP encodes integers without leading zero bytes, so `0` is
the empty byte string rather than `0x00`. Decoding an encoding that
carries a leading zero must fail, otherwise the specification tooling
would accept inputs that execution clients reject.

See https://github.com/ethereum/ethereum-rlp/issues/10.
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
    """Decode canonical `Uint` encodings with no leading zero byte."""
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
    """Reject integer encodings that carry a non-canonical leading zero."""
    with pytest.raises(DecodingError, match="non-canonical"):
        rlp.decode_to(integer_type, encoded)
