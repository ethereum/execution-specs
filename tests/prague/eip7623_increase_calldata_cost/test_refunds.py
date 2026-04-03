"""
Test [EIP-7623: Increase calldata cost](https://eips.ethereum.org/EIPS/eip-7623).
"""

from enum import Enum, Flag, auto
from typing import Dict, List

import pytest
from execution_testing import (
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.forks import Amsterdam, Prague

from .helpers import DataTestType
from .spec import ref_spec_7623

REFERENCE_SPEC_GIT_PATH = ref_spec_7623.git_path
REFERENCE_SPEC_VERSION = ref_spec_7623.version

ENABLE_FORK = Prague
pytestmark = [pytest.mark.valid_from(str(ENABLE_FORK))]


class RefundTestType(Enum):
    """Refund test type."""

    EXECUTION_GAS_MINUS_REFUND_GREATER_THAN_DATA_FLOOR = 0
    """
    The execution gas minus the refund is greater than the data floor, hence
    the execution gas cost is charged.
    """
    EXECUTION_GAS_MINUS_REFUND_LESS_THAN_DATA_FLOOR = 1
    """
    The execution gas minus the refund is less than the data floor, hence the
    data floor cost is charged.
    """
    EXECUTION_GAS_MINUS_REFUND_EQUAL_TO_DATA_FLOOR = 2
    """The execution gas minus the refund is equal to the data floor."""


class RefundType(Flag):
    """Refund type."""

    STORAGE_CLEAR = auto()
    """The storage is cleared from a non-zero value."""

    AUTHORIZATION_EXISTING_AUTHORITY = auto()
    """
    The authorization list contains an authorization where the authority exists
    in the state.
    """


@pytest.fixture
def data_test_type() -> DataTestType:
    """Return data test type."""
    return DataTestType.FLOOR_GAS_COST_GREATER_THAN_INTRINSIC_GAS


@pytest.fixture
def authorization_list(
    pre: Alloc, refund_type: RefundType
) -> List[AuthorizationTuple] | None:
    """
    Modify fixture from conftest to automatically read the refund_type
    information.
    """
    if RefundType.AUTHORIZATION_EXISTING_AUTHORITY not in refund_type:
        return None
    return [AuthorizationTuple(signer=pre.fund_eoa(1), address=Address(1))]


@pytest.fixture
def ty(refund_type: RefundType) -> int:
    """
    Modify fixture from conftest to automatically read the refund_type
    information.
    """
    if RefundType.AUTHORIZATION_EXISTING_AUTHORITY in refund_type:
        return 4
    return 2


@pytest.fixture
def state_gas_refund(fork: Fork, refund_type: RefundType) -> int:
    """Return the state gas refund (direct return, not subject to 1/5 cap)."""
    auth_existing = RefundType.AUTHORIZATION_EXISTING_AUTHORITY
    if fork >= Amsterdam and auth_existing in refund_type:
        gas_costs = fork.gas_costs()
        return gas_costs.REFUND_AUTH_PER_EXISTING_ACCOUNT
    return 0


@pytest.fixture
def max_refund(fork: Fork, refund_type: RefundType) -> int:
    """Return the max refund gas of the transaction."""
    gas_costs = fork.gas_costs()
    max_refund = (
        gas_costs.REFUND_STORAGE_CLEAR
        if RefundType.STORAGE_CLEAR in refund_type
        else 0
    )
    auth_existing = RefundType.AUTHORIZATION_EXISTING_AUTHORITY
    if fork < Amsterdam and auth_existing in refund_type:
        max_refund += gas_costs.REFUND_AUTH_PER_EXISTING_ACCOUNT
    return max_refund


@pytest.fixture
def prefix_code_gas(fork: Fork, refund_type: RefundType) -> int:
    """Return the minimum execution gas cost due to the refund type."""
    if RefundType.STORAGE_CLEAR in refund_type:
        # Minimum code to generate a storage clear is Op.SSTORE(0, 0).
        gas_costs = fork.gas_costs()
        return (
            gas_costs.GAS_COLD_STORAGE_ACCESS
            + gas_costs.GAS_STORAGE_RESET
            + (gas_costs.GAS_VERY_LOW * 2)
        )
    return 0


@pytest.fixture
def prefix_code(refund_type: RefundType) -> Bytecode:
    """Return the minimum execution gas cost due to the refund type."""
    if RefundType.STORAGE_CLEAR in refund_type:
        # Clear the storage to trigger a refund.
        return Op.SSTORE(0, 0)
    return Bytecode()


@pytest.fixture
def code_storage(refund_type: RefundType) -> Dict:
    """Return the minimum execution gas cost due to the refund type."""
    if RefundType.STORAGE_CLEAR in refund_type:
        # Pre-set the storage to be cleared.
        return {0: 1}
    return {}


@pytest.fixture
def contract_creating_tx() -> bool:
    """
    Override fixture in order to avoid a circular fixture dependency since none
    of these tests are contract creating transactions.
    """
    return False


@pytest.fixture
def intrinsic_gas_data_floor_minimum_delta() -> int:
    """
    Induce a minimum delta between the transaction intrinsic gas cost and the
    floor data gas cost.

    Since at least one of the cases requires some execution gas expenditure
    (SSTORE clearing), we need to introduce an increment of the floor data cost
    above the transaction intrinsic gas cost, otherwise the floor data cost
    would always be the below the execution gas cost even after the refund is
    applied.

    This value has been set as of Prague and should be adjusted if the gas
    costs change.
    """
    return 250


@pytest.fixture
def execution_gas_used(
    tx_intrinsic_gas_cost_before_execution: int,
    tx_floor_data_cost: int,
    max_refund: int,
    state_gas_refund: int,
    prefix_code_gas: int,
    refund_test_type: RefundTestType,
) -> int:
    """
    Return the amount of gas that needs to be consumed by the execution.

    This gas amount is on top of the transaction intrinsic gas cost.

    If this value were zero it would result in the refund being applied to the
    execution gas cost and the resulting amount being always below the floor
    data cost, hence we need to find a higher value in this function to ensure
    we get both scenarios where the refund drives the execution cost below the
    floor data cost and above the floor data cost.
    """

    def execution_gas_cost(execution_gas: int) -> int:
        total_gas_used = tx_intrinsic_gas_cost_before_execution + execution_gas
        effective_gas = total_gas_used - state_gas_refund
        capped_refund = min(max_refund, effective_gas // 5)
        return effective_gas - capped_refund

    execution_gas = prefix_code_gas

    assert execution_gas_cost(execution_gas) < tx_floor_data_cost, (
        "tx_floor_data_cost is too low, there might have been a gas cost "
        "change that caused this test to fail. Try increasing the "
        "intrinsic_gas_data_floor_minimum_delta fixture."
    )

    # Dumb for-loop to find the execution gas cost that will result in the
    # expected refund.
    while execution_gas_cost(execution_gas) < tx_floor_data_cost:
        execution_gas += 1
    if (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_EQUAL_TO_DATA_FLOOR
    ):
        return execution_gas
    elif (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_GREATER_THAN_DATA_FLOOR
    ):
        while execution_gas_cost(execution_gas) <= tx_floor_data_cost:
            execution_gas += 1
        return execution_gas
    elif (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_LESS_THAN_DATA_FLOOR
    ):
        return execution_gas - 1

    raise ValueError("Invalid refund test type")


@pytest.fixture
def refund(
    tx_intrinsic_gas_cost_before_execution: int,
    execution_gas_used: int,
    max_refund: int,
    state_gas_refund: int,
) -> int:
    """Return the refund gas of the transaction."""
    total_gas_used = (
        tx_intrinsic_gas_cost_before_execution + execution_gas_used
    )
    effective_gas = total_gas_used - state_gas_refund
    return min(max_refund, effective_gas // 5)


@pytest.fixture
def to(
    fork: Fork,
    pre: Alloc,
    execution_gas_used: int,
    prefix_code: Bytecode,
    prefix_code_gas: int,
    code_storage: Dict,
) -> Address | None:
    """
    Return a contract that consumes the expected execution gas.

    Uses a counting loop when the naive JUMPDEST approach would exceed the max
    contract code size. Loop gas costs are derived from the fork.
    """
    extra_gas = execution_gas_used - prefix_code_gas
    code = prefix_code + (Op.JUMPDEST * extra_gas) + Op.STOP
    if len(code) <= 24576:
        return pre.deploy_contract(code, storage=code_storage)

    loop_target = len(prefix_code) + len(Op.PUSH2(0))
    setup = Op.PUSH2(0)
    loop_body = (
        Op.JUMPDEST
        + Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.PUSH1(loop_target)
        + Op.JUMPI
    )
    teardown = Op.POP
    overhead = setup.gas_cost(fork) + teardown.gas_cost(fork)
    gas_per_iter = loop_body.gas_cost(fork)

    available = extra_gas - overhead
    iterations = available // gas_per_iter
    remaining = available % gas_per_iter

    code = (
        prefix_code
        + Op.PUSH2(iterations)
        + Op.JUMPDEST
        + Op.PUSH1(1)
        + Op.SWAP1
        + Op.SUB
        + Op.DUP1
        + Op.PUSH1(loop_target)
        + Op.JUMPI
        + Op.POP
        + (Op.JUMPDEST * remaining)
        + Op.STOP
    )
    return pre.deploy_contract(code, storage=code_storage)


@pytest.fixture
def tx_gas_limit(
    tx_intrinsic_gas_cost_including_floor_data_cost: int,
    tx_intrinsic_gas_cost_before_execution: int,
    execution_gas_used: int,
) -> int:
    """
    Gas limit for the transaction.

    The gas delta is added to the intrinsic gas cost to generate different test
    scenarios.
    """
    tx_gas_limit = tx_intrinsic_gas_cost_before_execution + execution_gas_used
    assert tx_gas_limit >= tx_intrinsic_gas_cost_including_floor_data_cost
    return tx_gas_limit


@pytest.mark.parametrize(
    "refund_test_type",
    [
        RefundTestType.EXECUTION_GAS_MINUS_REFUND_GREATER_THAN_DATA_FLOOR,
        RefundTestType.EXECUTION_GAS_MINUS_REFUND_LESS_THAN_DATA_FLOOR,
        RefundTestType.EXECUTION_GAS_MINUS_REFUND_EQUAL_TO_DATA_FLOOR,
    ],
)
@pytest.mark.parametrize(
    "refund_type",
    [
        RefundType.STORAGE_CLEAR,
        RefundType.STORAGE_CLEAR | RefundType.AUTHORIZATION_EXISTING_AUTHORITY,
        RefundType.AUTHORIZATION_EXISTING_AUTHORITY,
    ],
)
# TODO[EIP-8037]: Authorization state gas split affects
# refund calculations for Amsterdam.
@pytest.mark.valid_until("Osaka")
def test_gas_refunds_from_data_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    tx_floor_data_cost: int,
    tx_intrinsic_gas_cost_before_execution: int,
    execution_gas_used: int,
    refund: int,
    state_gas_refund: int,
    refund_test_type: RefundTestType,
) -> None:
    """
    Test gas refunds deducted from the execution gas cost and not the data
    floor.
    """
    gas_used = (
        tx_intrinsic_gas_cost_before_execution
        + execution_gas_used
        - state_gas_refund
        - refund
    )
    if (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_LESS_THAN_DATA_FLOOR
    ):
        assert gas_used < tx_floor_data_cost
    elif (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_GREATER_THAN_DATA_FLOOR
    ):
        assert gas_used > tx_floor_data_cost
    elif (
        refund_test_type
        == RefundTestType.EXECUTION_GAS_MINUS_REFUND_EQUAL_TO_DATA_FLOOR
    ):
        assert gas_used == tx_floor_data_cost
    else:
        raise ValueError("Invalid refund test type")
    if gas_used < tx_floor_data_cost:
        gas_used = tx_floor_data_cost
    # This is the actual test verification:
    #   - During test filling, the receipt returned by the transition tool
    #     (t8n) is verified against the expected receipt.
    #   - During test consumption, this is reflected in the balance difference
    #     and the state root.
    tx.expected_receipt = TransactionReceipt(cumulative_gas_used=gas_used)
    state_test(
        pre=pre,
        post={
            tx.to: {
                # Verify that the storage was cleared (for storage clear
                # refund). See `code_storage` fixture for more details.
                "storage": {0: 0},
            }
        },
        tx=tx,
    )
