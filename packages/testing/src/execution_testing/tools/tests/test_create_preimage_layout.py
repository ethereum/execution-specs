"""Test suite for `CreatePreimageLayout`."""

import pytest

from execution_testing.vm import Op

from ..tools_code.generators import CreatePreimageLayout


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
        nonce=Op.PUSH1(1),
        offset=offset,
    )
    assert layout.nonce_offset == offset + 32


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
