"""
Gas-limit boundary tests for EIP-2780.

Pin transactions one gas below the intrinsic charge layer to verify the
transaction is rejected by the pre-execution intrinsic gas check at
that boundary. Top-frame boundary OOGs are covered by the dedicated
top-frame charge tests in ``test_top_frame_charges.py``.
"""

import pytest
from execution_testing import (
    Alloc,
    Fork,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import RECIPIENT_TYPES_NON_CREATE, setup_target
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.exception_test
@pytest.mark.parametrize("recipient_type", RECIPIENT_TYPES_NON_CREATE)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_intrinsic_gas_floor_boundary(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_type: RecipientType,
    value: int,
) -> None:
    """
    Reject when ``gas_limit = intrinsic_gas - 1``.

    The transaction never enters the EVM; it is rejected by the
    pre-execution intrinsic gas check.
    """
    sender = pre.fund_eoa(10**18)
    target = setup_target(pre, recipient_type, sender)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=intrinsic_gas - 1,
        gas_price=1_000_000_000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post={})


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_intrinsic_gas_floor_boundary_contract_creation(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    value: int,
) -> None:
    """
    Reject a contract-creation transaction when
    ``gas_limit = intrinsic_gas - 1``.

    A creation tx's intrinsic includes the ``NEW_ACCOUNT`` state gas, so
    the pre-execution check rejects against the combined
    ``regular + state`` intrinsic. The init code never runs.
    """
    sender = pre.fund_eoa(10**18)
    init_code = Op.STOP

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=init_code,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=init_code,
        gas_limit=intrinsic_gas - 1,
        gas_price=1_000_000_000,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW,
    )

    state_test(pre=pre, tx=tx, post={})
