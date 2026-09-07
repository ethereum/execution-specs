"""
Tests for the gas-limit boundary between the intrinsic cost and the calldata
floor in
[EIP-7976: Increase Calldata Floor Cost](https://eips.ethereum.org/EIPS/eip-7976).
"""

import pytest
from execution_testing import (
    Alloc,
    Bytes,
    EIPChecklist,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = [
    pytest.mark.valid_from("EIP7976"),
    pytest.mark.inclusion_test,
]

# Enough zero bytes for the floor to land well above the intrinsic cost.
ZERO_BYTES = 1000


@pytest.fixture
def tx_data() -> Bytes:
    """Calldata whose floor cost exceeds the intrinsic cost."""
    return Bytes(b"\x00" * ZERO_BYTES)


@pytest.fixture
def intrinsic_gas(fork: Fork, tx_data: Bytes) -> int:
    """Intrinsic cost charged before execution, floor excluded."""
    return fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data,
        return_cost_deducted_prior_execution=True,
    )


@pytest.fixture
def floor_gas(fork: Fork, tx_data: Bytes, intrinsic_gas: int) -> int:
    """Calldata floor cost, asserted to sit above the intrinsic cost."""
    floor = fork.transaction_data_floor_cost_calculator()(data=tx_data)
    assert floor > intrinsic_gas
    return floor


@EIPChecklist.TransactionType.Test.IntrinsicValidity.DataFloorAboveIntrinsicGasCost.GasLimitIntrinsic()  # noqa: E501
@pytest.mark.exception_test
def test_gas_limit_equals_intrinsic_below_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data: Bytes,
    intrinsic_gas: int,
    floor_gas: int,
) -> None:
    """
    Reject a transaction whose gas limit covers the intrinsic cost exactly
    but not the calldata floor.

    Type-0 only on purpose; the floor-minus-one arm across all transaction
    types lives in `test_transaction_validity.py`.
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(amount=0),
        data=tx_data,
        gas_limit=intrinsic_gas,
        error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
    )
    state_test(pre=pre, post={}, tx=tx)


@EIPChecklist.TransactionType.Test.IntrinsicValidity.DataFloorAboveIntrinsicGasCost.GasLimitFloor()  # noqa: E501
def test_gas_limit_equals_floor_above_intrinsic(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data: Bytes,
    floor_gas: int,
) -> None:
    """
    Accept a transaction whose gas limit equals the calldata floor and bill
    the floor rather than the lower intrinsic cost.
    """
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(amount=0),
        data=tx_data,
        gas_limit=floor_gas,
        expected_receipt=TransactionReceipt(cumulative_gas_used=floor_gas),
    )
    state_test(pre=pre, post={}, tx=tx)
