"""Test the RLP size helpers in `serialization`."""

from typing import Any

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import U64, U256, Uint

from ..serialization import KnownEncodedSize, encoded_size


@pytest.mark.parametrize(
    "raw_data",
    [
        pytest.param(b"", id="empty_bytes"),
        pytest.param(b"\x00", id="single_byte_zero"),
        pytest.param(b"\x7f", id="single_byte_below_0x80"),
        pytest.param(b"\x80", id="single_byte_0x80"),
        pytest.param(b"\x01" * 55, id="bytes_55"),
        pytest.param(b"\x01" * 56, id="bytes_56"),
        pytest.param(b"\x01" * 256, id="bytes_256"),
        pytest.param(b"\x01" * 70_000, id="bytes_70000"),
        pytest.param([], id="empty_list"),
        pytest.param([b"\x01" * 53], id="list_payload_55"),
        pytest.param([b"\x01" * 54], id="list_payload_56"),
        pytest.param([b"\x01" * 254], id="list_payload_256"),
        pytest.param([b"\x01", [b"", [b"\x02" * 60]]], id="nested_list"),
        pytest.param(Uint(0), id="uint_zero"),
        pytest.param(Uint(0x7F), id="uint_0x7f"),
        pytest.param(Uint(0x80), id="uint_0x80"),
        pytest.param(U64(2**64 - 1), id="u64_max"),
        pytest.param(U256(2**256 - 1), id="u256_max"),
        pytest.param(True, id="bool_true"),
        pytest.param(False, id="bool_false"),
        pytest.param("a" * 56, id="str_56"),
    ],
)
def test_encoded_size_matches_encode(raw_data: Any) -> None:
    """Test that `encoded_size` equals the length of the real encoding."""
    assert encoded_size(raw_data) == len(eth_rlp.encode(raw_data))


@pytest.mark.parametrize("payload_size", [1, 55, 56, 256])
def test_known_encoded_size_placeholder(payload_size: int) -> None:
    """Test that a placeholder counts as the item it stands in for."""
    item = b"\x01" * payload_size
    placeholder = KnownEncodedSize(len(eth_rlp.encode(item)))
    assert encoded_size([b"\x02", placeholder]) == len(
        eth_rlp.encode([b"\x02", item])
    )
