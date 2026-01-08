"""
Tests for ethereum.utils.address module.

These tests verify the address utility functions work correctly.
"""

import pytest
from ethereum_types.bytes import Bytes20
from ethereum_types.numeric import Uint

from ethereum.utils.address import (
    ADDRESS_BYTE_LENGTH,
    address_to_uint,
    is_precompile_address,
    is_valid_address_length,
    is_valid_checksum_address,
    is_zero_address,
    to_checksum_address,
    uint_to_address,
)


class TestIsValidAddressLength:
    """Tests for is_valid_address_length function."""

    def test_valid_address_length(self) -> None:
        """Test with exactly 20 bytes."""
        assert is_valid_address_length(b"\x00" * 20) is True

    def test_too_short(self) -> None:
        """Test with less than 20 bytes."""
        assert is_valid_address_length(b"\x00" * 19) is False

    def test_too_long(self) -> None:
        """Test with more than 20 bytes."""
        assert is_valid_address_length(b"\x00" * 21) is False

    def test_empty(self) -> None:
        """Test with empty bytes."""
        assert is_valid_address_length(b"") is False


class TestIsZeroAddress:
    """Tests for is_zero_address function."""

    def test_zero_address(self) -> None:
        """Test with actual zero address."""
        zero_addr = Bytes20(b"\x00" * 20)
        assert is_zero_address(zero_addr) is True

    def test_non_zero_address(self) -> None:
        """Test with non-zero address."""
        non_zero = Bytes20(b"\x01" + b"\x00" * 19)
        assert is_zero_address(non_zero) is False

    def test_all_ones(self) -> None:
        """Test with all 0xFF bytes."""
        all_ones = Bytes20(b"\xff" * 20)
        assert is_zero_address(all_ones) is False


class TestIsPrecompileAddress:
    """Tests for is_precompile_address function."""

    def test_precompile_one(self) -> None:
        """Test address 0x01 is a precompile."""
        addr = Bytes20(b"\x00" * 19 + b"\x01")
        assert is_precompile_address(addr) is True

    def test_precompile_ten(self) -> None:
        """Test address 0x0a is a precompile (default max)."""
        addr = Bytes20(b"\x00" * 19 + b"\x0a")
        assert is_precompile_address(addr) is True

    def test_not_precompile_eleven(self) -> None:
        """Test address 0x0b is not a precompile (default max=10)."""
        addr = Bytes20(b"\x00" * 19 + b"\x0b")
        assert is_precompile_address(addr) is False

    def test_zero_not_precompile(self) -> None:
        """Test zero address is not a precompile."""
        addr = Bytes20(b"\x00" * 20)
        assert is_precompile_address(addr) is False

    def test_custom_max_precompile(self) -> None:
        """Test with custom max_precompile parameter."""
        addr = Bytes20(b"\x00" * 19 + b"\x0f")
        assert is_precompile_address(addr, max_precompile=15) is True
        assert is_precompile_address(addr, max_precompile=10) is False

    def test_high_address_not_precompile(self) -> None:
        """Test that a regular address is not a precompile."""
        # Address with non-zero bytes in first 19 positions
        addr = Bytes20(b"\x01" + b"\x00" * 18 + b"\x01")
        assert is_precompile_address(addr) is False


class TestAddressToUint:
    """Tests for address_to_uint function."""

    def test_zero_address(self) -> None:
        """Test converting zero address to uint."""
        addr = Bytes20(b"\x00" * 20)
        assert address_to_uint(addr) == Uint(0)

    def test_address_one(self) -> None:
        """Test converting address 0x01 to uint."""
        addr = Bytes20(b"\x00" * 19 + b"\x01")
        assert address_to_uint(addr) == Uint(1)

    def test_max_address(self) -> None:
        """Test converting max address (all 0xFF) to uint."""
        addr = Bytes20(b"\xff" * 20)
        expected = Uint(2**160 - 1)
        assert address_to_uint(addr) == expected


class TestUintToAddress:
    """Tests for uint_to_address function."""

    def test_zero(self) -> None:
        """Test converting 0 to address."""
        addr = uint_to_address(Uint(0))
        assert addr == Bytes20(b"\x00" * 20)

    def test_one(self) -> None:
        """Test converting 1 to address."""
        addr = uint_to_address(Uint(1))
        assert addr == Bytes20(b"\x00" * 19 + b"\x01")

    def test_roundtrip(self) -> None:
        """Test converting address to uint and back."""
        original = Bytes20(b"\xde\xad\xbe\xef" + b"\x00" * 16)
        uint_val = address_to_uint(original)
        result = uint_to_address(uint_val)
        assert result == original


class TestToChecksumAddress:
    """Tests for to_checksum_address function."""

    def test_eip55_example(self) -> None:
        """Test with EIP-55 example address."""
        # This is an example from EIP-55
        addr_bytes = bytes.fromhex("5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed")
        addr = Bytes20(addr_bytes)
        result = to_checksum_address(addr)
        assert result == "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"

    def test_zero_address(self) -> None:
        """Test checksum of zero address."""
        addr = Bytes20(b"\x00" * 20)
        result = to_checksum_address(addr)
        assert result == "0x" + "0" * 40


class TestIsValidChecksumAddress:
    """Tests for is_valid_checksum_address function."""

    def test_valid_checksum(self) -> None:
        """Test with valid checksummed address."""
        assert is_valid_checksum_address(
            "0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        ) is True

    def test_invalid_checksum(self) -> None:
        """Test with invalid checksum (all lowercase)."""
        assert is_valid_checksum_address(
            "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
        ) is False

    def test_without_prefix(self) -> None:
        """Test address without 0x prefix."""
        assert is_valid_checksum_address(
            "5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed"
        ) is True

    def test_wrong_length(self) -> None:
        """Test with wrong length address."""
        assert is_valid_checksum_address("0x5aAeb6053F3E94C9b9") is False

    def test_invalid_hex(self) -> None:
        """Test with invalid hex characters."""
        assert is_valid_checksum_address("0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG") is False
