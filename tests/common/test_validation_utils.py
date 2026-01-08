"""
Tests for ethereum.utils.validation module.

These tests verify the validation utility functions work correctly.
"""

import pytest
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.utils.validation import (
    MAX_BLOCK_NUMBER,
    MAX_GAS_LIMIT,
    MAX_NONCE,
    MAX_U64,
    MAX_U256,
    is_valid_base_fee,
    is_valid_block_number,
    is_valid_chain_id,
    is_valid_gas_limit,
    is_valid_hash,
    is_valid_nonce,
    is_valid_u64,
    is_valid_u256,
    is_zero_hash,
    validate_transaction_value,
)


class TestIsValidGasLimit:
    """Tests for is_valid_gas_limit function."""

    def test_valid_gas_limit(self) -> None:
        """Test with a typical valid gas limit."""
        assert is_valid_gas_limit(21000) is True

    def test_maximum_gas_limit(self) -> None:
        """Test with maximum gas limit."""
        assert is_valid_gas_limit(MAX_GAS_LIMIT) is True

    def test_zero_gas_limit(self) -> None:
        """Test with zero gas limit (invalid)."""
        assert is_valid_gas_limit(0) is False

    def test_negative_gas_limit(self) -> None:
        """Test with negative gas limit (invalid)."""
        assert is_valid_gas_limit(-1) is False

    def test_exceeds_maximum(self) -> None:
        """Test with gas limit exceeding maximum."""
        assert is_valid_gas_limit(MAX_GAS_LIMIT + 1) is False

    def test_with_uint(self) -> None:
        """Test with Uint type."""
        assert is_valid_gas_limit(Uint(30000000)) is True


class TestIsValidNonce:
    """Tests for is_valid_nonce function."""

    def test_zero_nonce(self) -> None:
        """Test with zero nonce (valid)."""
        assert is_valid_nonce(0) is True

    def test_typical_nonce(self) -> None:
        """Test with a typical nonce value."""
        assert is_valid_nonce(100) is True

    def test_maximum_nonce(self) -> None:
        """Test with maximum valid nonce (EIP-2681)."""
        assert is_valid_nonce(MAX_NONCE) is True

    def test_exceeds_maximum(self) -> None:
        """Test with nonce exceeding maximum."""
        assert is_valid_nonce(MAX_NONCE + 1) is False

    def test_negative_nonce(self) -> None:
        """Test with negative nonce (invalid)."""
        assert is_valid_nonce(-1) is False


class TestIsValidBlockNumber:
    """Tests for is_valid_block_number function."""

    def test_genesis_block(self) -> None:
        """Test with genesis block (0)."""
        assert is_valid_block_number(0) is True

    def test_typical_block(self) -> None:
        """Test with a typical block number."""
        assert is_valid_block_number(19000000) is True

    def test_maximum_block(self) -> None:
        """Test with maximum block number."""
        assert is_valid_block_number(MAX_BLOCK_NUMBER) is True

    def test_negative_block(self) -> None:
        """Test with negative block number (invalid)."""
        assert is_valid_block_number(-1) is False


class TestIsValidU256:
    """Tests for is_valid_u256 function."""

    def test_zero(self) -> None:
        """Test with zero."""
        assert is_valid_u256(0) is True

    def test_maximum(self) -> None:
        """Test with maximum U256 value."""
        assert is_valid_u256(MAX_U256) is True

    def test_exceeds_maximum(self) -> None:
        """Test with value exceeding maximum."""
        assert is_valid_u256(MAX_U256 + 1) is False

    def test_negative(self) -> None:
        """Test with negative value."""
        assert is_valid_u256(-1) is False


class TestIsValidU64:
    """Tests for is_valid_u64 function."""

    def test_zero(self) -> None:
        """Test with zero."""
        assert is_valid_u64(0) is True

    def test_maximum(self) -> None:
        """Test with maximum U64 value."""
        assert is_valid_u64(MAX_U64) is True

    def test_exceeds_maximum(self) -> None:
        """Test with value exceeding maximum."""
        assert is_valid_u64(MAX_U64 + 1) is False

    def test_negative(self) -> None:
        """Test with negative value."""
        assert is_valid_u64(-1) is False


class TestIsValidHash:
    """Tests for is_valid_hash function."""

    def test_valid_hash(self) -> None:
        """Test with exactly 32 bytes."""
        assert is_valid_hash(b"\x00" * 32) is True

    def test_too_short(self) -> None:
        """Test with less than 32 bytes."""
        assert is_valid_hash(b"\x00" * 31) is False

    def test_too_long(self) -> None:
        """Test with more than 32 bytes."""
        assert is_valid_hash(b"\x00" * 33) is False

    def test_empty(self) -> None:
        """Test with empty bytes."""
        assert is_valid_hash(b"") is False


class TestIsZeroHash:
    """Tests for is_zero_hash function."""

    def test_zero_hash(self) -> None:
        """Test with zero hash."""
        zero_hash = Bytes32(b"\x00" * 32)
        assert is_zero_hash(zero_hash) is True

    def test_non_zero_hash(self) -> None:
        """Test with non-zero hash."""
        non_zero = Bytes32(b"\x01" + b"\x00" * 31)
        assert is_zero_hash(non_zero) is False

    def test_all_ones(self) -> None:
        """Test with all 0xFF bytes."""
        all_ones = Bytes32(b"\xff" * 32)
        assert is_zero_hash(all_ones) is False


class TestIsValidChainId:
    """Tests for is_valid_chain_id function."""

    def test_mainnet(self) -> None:
        """Test with mainnet chain ID (1)."""
        assert is_valid_chain_id(1) is True

    def test_sepolia(self) -> None:
        """Test with Sepolia chain ID."""
        assert is_valid_chain_id(11155111) is True

    def test_zero(self) -> None:
        """Test with zero (invalid)."""
        assert is_valid_chain_id(0) is False

    def test_negative(self) -> None:
        """Test with negative value (invalid)."""
        assert is_valid_chain_id(-1) is False

    def test_maximum(self) -> None:
        """Test with maximum uint64 value."""
        assert is_valid_chain_id(MAX_U64) is True


class TestValidateTransactionValue:
    """Tests for validate_transaction_value function."""

    def test_zero_value(self) -> None:
        """Test with zero value (valid for contract calls)."""
        assert validate_transaction_value(0) is True

    def test_typical_value(self) -> None:
        """Test with a typical ETH transfer value."""
        one_eth = 10**18  # 1 ETH in wei
        assert validate_transaction_value(one_eth) is True

    def test_maximum_value(self) -> None:
        """Test with maximum U256 value."""
        assert validate_transaction_value(MAX_U256) is True

    def test_negative_value(self) -> None:
        """Test with negative value (invalid)."""
        assert validate_transaction_value(-1) is False


class TestIsValidBaseFee:
    """Tests for is_valid_base_fee function."""

    def test_minimum_base_fee(self) -> None:
        """Test with minimum valid base fee (1 wei)."""
        assert is_valid_base_fee(1) is True

    def test_typical_base_fee(self) -> None:
        """Test with a typical base fee (10 gwei)."""
        ten_gwei = 10 * 10**9
        assert is_valid_base_fee(ten_gwei) is True

    def test_zero_base_fee(self) -> None:
        """Test with zero base fee (invalid post-London)."""
        assert is_valid_base_fee(0) is False

    def test_negative_base_fee(self) -> None:
        """Test with negative base fee (invalid)."""
        assert is_valid_base_fee(-1) is False
