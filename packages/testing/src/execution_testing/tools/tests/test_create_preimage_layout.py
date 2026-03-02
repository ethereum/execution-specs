"""Test suite for `CreatePreimageLayout` and `_rlp_encode_nonce`."""

import ethereum_rlp as eth_rlp
import pytest

from execution_testing.test_types.utils import int_to_bytes
from execution_testing.vm import Op

from ..tools_code.generators import CreatePreimageLayout, _rlp_encode_nonce


@pytest.mark.parametrize(
    "nonce,expected",
    [
        pytest.param(0, b"\x80", id="zero"),
        pytest.param(1, b"\x01", id="one"),
        pytest.param(127, b"\x7f", id="max-single-byte"),
        pytest.param(128, b"\x81\x80", id="two-byte-min"),
        pytest.param(255, b"\x81\xff", id="max-one-byte-value"),
        pytest.param(256, b"\x82\x01\x00", id="two-byte-big-endian"),
        pytest.param(3515, b"\x82\x0d\xbb", id="multi-byte"),
        pytest.param(
            2**64 - 1,
            b"\x88" + b"\xff" * 8,
            id="max-nonce-8-bytes",
        ),
    ],
)
def test_rlp_encode_nonce_expected_values(nonce: int, expected: bytes) -> None:
    """Test `_rlp_encode_nonce` against known expected values."""
    assert _rlp_encode_nonce(nonce) == expected


@pytest.mark.parametrize(
    "nonce",
    [0, 1, 127, 128, 255, 256, 3515, 2**64 - 1],
)
def test_rlp_encode_nonce_matches_eth_rlp(nonce: int) -> None:
    """Test `_rlp_encode_nonce` matches `ethereum_rlp.encode`."""
    assert _rlp_encode_nonce(nonce) == eth_rlp.encode(int_to_bytes(nonce))


@pytest.mark.parametrize(
    "nonce",
    [0, 1, 127, 128, 255, 256, 3515, 2**64 - 1],
)
def test_create_preimage_layout_preimage_size(nonce: int) -> None:
    """Test `CreatePreimageLayout.preimage_size` matches expected value."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=nonce,
    )
    assert layout.preimage_size == 22 + len(_rlp_encode_nonce(nonce))


@pytest.mark.parametrize(
    "offset",
    [
        pytest.param(0, id="zero-offset"),
        pytest.param(32, id="32-offset"),
        pytest.param(100, id="100-offset"),
    ],
)
def test_create_preimage_layout_nonce_offset(offset: int) -> None:
    """Test `CreatePreimageLayout.nonce_offset` equals offset + 32."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=0,
        offset=offset,
    )
    assert layout.nonce_offset == offset + 32


@pytest.mark.parametrize(
    "offset",
    [
        pytest.param(0, id="zero-offset"),
        pytest.param(32, id="32-offset"),
    ],
)
def test_create_preimage_layout_address_op(offset: int) -> None:
    """Test `CreatePreimageLayout.address_op` returns correct bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=1,
        offset=offset,
    )
    address_mask = (1 << 160) - 1
    expected = Op.AND(
        address_mask,
        Op.SHA3(
            offset=offset + 10,
            size=layout.preimage_size,
            data_size=layout.preimage_size,
        ),
    )
    assert bytes(layout.address_op()) == bytes(expected)


@pytest.mark.parametrize(
    "nonce",
    [
        pytest.param(0, id="zero-nonce"),
        pytest.param(1, id="nonce-1"),
        pytest.param(127, id="nonce-127"),
        pytest.param(128, id="nonce-128"),
        pytest.param(255, id="nonce-255"),
    ],
)
def test_create_preimage_layout_address(nonce: int) -> None:
    """
    Test `CreatePreimageLayout` preimage size matches the canonical RLP
    encoding for the given nonce.
    """
    sender_int = 0xDEADBEEF
    layout = CreatePreimageLayout(
        sender_address=sender_int,
        nonce=nonce,
    )
    expected_rlp = eth_rlp.encode(
        [sender_int.to_bytes(20, "big"), int_to_bytes(nonce)]
    )
    assert layout.preimage_size == len(expected_rlp)


def test_create_preimage_layout_dynamic_is_bytecode() -> None:
    """Test that dynamic nonce layout produces valid Bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    assert len(layout) > 0
    assert layout._dynamic is True
    assert layout.preimage_size == 0


def test_create_preimage_layout_dynamic_address_op() -> None:
    """Test that dynamic address_op uses MLOAD for preimage size."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    address_mask = (1 << 160) - 1
    expected = Op.AND(
        address_mask,
        Op.SHA3(
            offset=10,
            size=Op.MLOAD(64),
            data_size=25,
        ),
    )
    assert bytes(layout.address_op()) == bytes(expected)


def test_create_preimage_layout_set_nonce_op() -> None:
    """Test that set_nonce_op returns valid Bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    result = layout.set_nonce_op(42)
    assert len(result) > 0


def test_create_preimage_layout_increment_nonce_op() -> None:
    """Test that increment_nonce_op returns valid Bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    result = layout.increment_nonce_op()
    assert len(result) > 0


def test_create_preimage_layout_static_set_nonce_switches() -> None:
    """Test that set_nonce_op on static layout switches to dynamic."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=0,
    )
    assert layout._dynamic is False
    layout.set_nonce_op(42)
    assert layout._dynamic is True
