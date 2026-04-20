"""Regression tests for Amsterdam transaction validation helper seams."""

from typing import Any

import pytest
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import U64, U256, Uint

from ethereum.exceptions import (
    InsufficientTransactionGasError,
    NonceOverflowError,
)
from ethereum.forks.amsterdam.exceptions import (
    InitCodeTooLargeError,
    TransactionGasLimitExceededError,
)
from ethereum.forks.amsterdam.transactions import (
    TX_MAX_GAS_LIMIT,
    LegacyTransaction,
    calculate_intrinsic_cost,
    validate_transaction,
    validate_transaction_gas,
    validate_transaction_gas_limit,
    validate_transaction_init_code_size,
    validate_transaction_nonce,
    validate_transaction_rules,
)
from ethereum.forks.amsterdam.vm.interpreter import MAX_INIT_CODE_SIZE
from ethereum.state import Address


def make_legacy_transaction(**overrides: Any) -> LegacyTransaction:
    """Build a baseline legacy transaction for validation tests."""
    fields: dict[str, Any] = {
        "nonce": U256(0),
        "gas_price": Uint(1),
        "gas": Uint(21000),
        "to": Address(b"\x11" * 20),
        "value": U256(0),
        "data": Bytes(b""),
        "v": U256(27),
        "r": U256(1),
        "s": U256(2),
    }
    fields.update(overrides)
    return LegacyTransaction(**fields)


def test_validate_transaction_gas_raises_for_insufficient_gas() -> None:
    """Gas validation raises when tx gas is below intrinsic requirements."""
    tx = make_legacy_transaction(gas=Uint(20999))
    intrinsic_gas, data_floor_gas_cost = calculate_intrinsic_cost(tx)

    with pytest.raises(InsufficientTransactionGasError):
        validate_transaction_gas(tx, intrinsic_gas, data_floor_gas_cost)


def test_validate_transaction_nonce_raises_for_overflow() -> None:
    """Nonce validation raises when the transaction nonce overflows."""
    tx = make_legacy_transaction(nonce=U256(U64.MAX_VALUE))

    with pytest.raises(NonceOverflowError):
        validate_transaction_nonce(tx)


def test_validate_transaction_init_code_size_raises() -> None:
    """Initcode validation raises for oversized contract-creation payloads."""
    tx = make_legacy_transaction(
        to=Bytes0(b""),
        data=Bytes(b"\x00" * (MAX_INIT_CODE_SIZE + 1)),
    )

    with pytest.raises(InitCodeTooLargeError):
        validate_transaction_init_code_size(tx)


def test_validate_transaction_gas_limit_raises_for_excessive_limit() -> None:
    """Gas-limit validation raises when the tx gas exceeds the fork cap."""
    tx = make_legacy_transaction(gas=TX_MAX_GAS_LIMIT + Uint(1))

    with pytest.raises(TransactionGasLimitExceededError):
        validate_transaction_gas_limit(tx)


def test_validate_transaction_preserves_validation_order() -> None:
    """Validation order remains gas, nonce, initcode size, then gas limit."""
    tx = make_legacy_transaction(
        nonce=U256(U64.MAX_VALUE),
        gas=TX_MAX_GAS_LIMIT + Uint(1),
    )

    with pytest.raises(NonceOverflowError):
        validate_transaction(tx)


def test_validate_transaction_returns_expected_costs() -> None:
    """Top-level validation returns the same intrinsic and floor costs."""
    tx = make_legacy_transaction()

    assert validate_transaction(tx) == calculate_intrinsic_cost(tx)


def test_validate_transaction_rules_accepts_valid_transaction() -> None:
    """
    Grouped validation helper accepts a transaction that passes all checks.
    """
    tx = make_legacy_transaction()
    intrinsic_gas, data_floor_gas_cost = calculate_intrinsic_cost(tx)

    assert (
        validate_transaction_rules(tx, intrinsic_gas, data_floor_gas_cost)
        is None
    )
