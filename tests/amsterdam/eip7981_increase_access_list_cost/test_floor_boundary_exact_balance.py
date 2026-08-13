"""
Tests for floor-boundary rejection with exact-balance funding in
[EIP-7981: Increase Access List Cost](https://eips.ethereum.org/EIPS/eip-7981).
"""

import pytest
from execution_testing import (
    AccessList,
    Address,
    Alloc,
    Bytes,
    EIPChecklist,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .spec import ref_spec_7981

REFERENCE_SPEC_GIT_PATH = ref_spec_7981.git_path
REFERENCE_SPEC_VERSION = ref_spec_7981.version

pytestmark = pytest.mark.valid_at("EIP7981")


@pytest.mark.inclusion_test
@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "tx_type",
    [pytest.param(1, id="type_1"), pytest.param(2, id="type_2")],
)
@pytest.mark.parametrize(
    "nonzero_bytes",
    [
        # Must be large enough that the floor midpoint chosen below
        # stays above the access-list intrinsic cost (asserted in the
        # test body): each nonzero byte adds 64 gas to the floor but
        # only 16 to the intrinsic cost.
        pytest.param(1700, id="1700_nonzero_bytes"),
        pytest.param(2000, id="2000_nonzero_bytes"),
    ],
)
def test_below_amsterdam_floor_with_access_list_exact_balance(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_type: int,
    nonzero_bytes: int,
) -> None:
    """Reject when gas_limit sits in EIP-7981 access-list-byte floor gap."""
    access_list = [
        AccessList(
            address=Address(1),
            storage_keys=[Hash(k) for k in range(10)],
        )
    ]
    tx_data = Bytes(b"\x01" * nonzero_bytes)
    intrinsic_execution = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data,
        access_list=access_list,
        return_cost_deducted_prior_execution=True,
    )
    floor_calc = fork.transaction_data_floor_cost_calculator()
    amsterdam_floor = floor_calc(data=tx_data, access_list=access_list)
    amsterdam_floor_no_al = floor_calc(data=tx_data)
    # Pin gas_limit inside the access-list-byte uplift gap so an
    # implementation that omits this term from its floor accepts.
    gas_limit = (amsterdam_floor_no_al + amsterdam_floor) // 2
    assert intrinsic_execution <= gas_limit < amsterdam_floor
    assert gas_limit >= amsterdam_floor_no_al

    gas_price = 10
    sender = pre.fund_eoa(amount=gas_limit * gas_price)
    if tx_type == 1:
        fee_args: dict = {"gas_price": gas_price}
    else:
        fee_args = {
            "max_fee_per_gas": gas_price,
            "max_priority_fee_per_gas": 0,
        }
    tx = Transaction(
        ty=tx_type,
        sender=sender,
        to=pre.fund_eoa(amount=0),
        data=tx_data,
        gas_limit=gas_limit,
        access_list=access_list,
        error=TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST,
        **fee_args,
    )

    state_test(pre=pre, post={}, tx=tx)
