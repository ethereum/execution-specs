"""
Tests for floor-boundary rejection with exact-balance funding in
[EIP-7976: Increase Calldata Floor Cost](https://eips.ethereum.org/EIPS/eip-7976).
"""

import pytest
from execution_testing import (
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from ...prague.eip7623_increase_calldata_cost.spec import Spec as Spec7623
from .spec import ref_spec_7976

REFERENCE_SPEC_GIT_PATH = ref_spec_7976.git_path
REFERENCE_SPEC_VERSION = ref_spec_7976.version

pytestmark = pytest.mark.valid_at("EIP7976")


@pytest.mark.inclusion_test
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "zero_bytes",
    [
        pytest.param(200, id="200_zero_bytes"),
        pytest.param(1000, id="1000_zero_bytes"),
    ],
)
def test_below_amsterdam_floor_with_exact_balance_sender(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    zero_bytes: int,
) -> None:
    """
    Reject when gas_limit sits between Prague and Amsterdam floor.

    EIP-7976 raises the per-byte calldata floor cost. A transaction
    with `gas_limit` in `[Prague_floor, Amsterdam_floor)` must reject
    with `INTRINSIC_GAS_BELOW_FLOOR_GAS_COST`. The sender is funded
    with exactly `gas_limit * gas_price` so an implementation that
    uses the Prague floor cannot fall back to silent execution.

    Type-0 only on purpose; broader type-1/2/3/4 coverage lives in
    `test_transaction_validity.py`.
    """
    tx_data = Bytes(b"\x00" * zero_bytes)
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data,
        return_cost_deducted_prior_execution=True,
    )
    amsterdam_floor = fork.transaction_data_floor_cost_calculator()(
        data=tx_data,
    )
    # Prague counts each zero byte as one token at TX_DATA_TOKEN_FLOOR
    # gas/token. Cannot be derived from amsterdam_floor because EIP-7976
    # changes both the per-token rate (10->16) and the floor tokenization
    # (zero/nonzero both weighted by 4).
    prague_floor = 21000 + Spec7623.TX_DATA_TOKEN_FLOOR * zero_bytes
    gas_limit = (prague_floor + amsterdam_floor) // 2
    assert intrinsic_execution <= gas_limit
    assert prague_floor <= gas_limit < amsterdam_floor

    gas_price = 10
    sender = pre.fund_eoa(amount=gas_limit * gas_price)
    tx = Transaction(
        sender=sender,
        to=pre.fund_eoa(amount=0),
        data=tx_data,
        gas_limit=gas_limit,
        gas_price=gas_price,
        error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
    )

    state_test(pre=pre, post={}, tx=tx)
