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
    GasConsumer,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)
from execution_testing.forks import Prague

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
    pre: Alloc, refund_type: RefundType, fork: Fork
) -> List[AuthorizationTuple] | None:
    """
    Modify fixture from conftest to automatically read the refund_type
    information.

    On EIP-8037 / EIP-2780 an existing funded authority pays only the
    top-frame ``AUTH_BASE`` (no ``NEW_ACCOUNT`` / ``ACCOUNT_WRITE``, and no
    existing-authority refund), so the tuple is annotated accordingly.
    """
    if RefundType.AUTHORIZATION_EXISTING_AUTHORITY not in refund_type:
        return None
    signer = pre.fund_eoa(1)
    if fork.is_eip_enabled(8037):
        return [
            AuthorizationTuple(
                signer=signer,
                address=Address(1),
                creates_account=False,
                writes_delegation=True,
            )
        ]
    return [AuthorizationTuple(signer=signer, address=Address(1))]


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
def top_frame_execution(
    fork: Fork, authorization_list: List[AuthorizationTuple] | None
) -> int:
    """Top-frame execution gas charged for authorizations (EIP-8037)."""
    if not authorization_list or not fork.is_eip_enabled(8037):
        return 0
    return fork.transaction_top_frame_execution_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )


@pytest.fixture
def top_frame_state(
    fork: Fork, authorization_list: List[AuthorizationTuple] | None
) -> int:
    """Top-frame state gas charged for authorizations (EIP-8037)."""
    if not authorization_list or not fork.is_eip_enabled(8037):
        return 0
    return fork.transaction_top_frame_state_gas(
        recipient_type=RecipientType.CONTRACT,
        authorizations=authorization_list,
    )


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
    # Pre-EIP-8037: existing-authority auth refund lands in refund_counter
    # (EIP-3529 1/5 cap). EIP-8037 / EIP-2780 charge AUTH_BASE directly at
    # the top frame with no existing-authority refund.
    if not fork.is_eip_enabled(8037) and auth_existing in refund_type:
        max_refund += gas_costs.REFUND_AUTH_PER_EXISTING_ACCOUNT
    return max_refund


@pytest.fixture
def prefix_code_gas(fork: Fork, refund_type: RefundType) -> int:
    """Return the minimum execution gas cost due to the refund type."""
    if RefundType.STORAGE_CLEAR in refund_type:
        # Minimum code to generate a storage clear is Op.SSTORE(0, 0).
        return (
            Op.SSTORE(
                key_warm=False,
                original_value=1,
                new_value=0,
            )
            + Op.PUSH1(0) * 2
        ).gas_cost(fork)
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
def intrinsic_gas_data_floor_minimum_delta(
    fork: Fork,
    prefix_code_gas: int,
    top_frame_execution: int,
    top_frame_state: int,
) -> int:
    """
    Induce a minimum delta between the transaction intrinsic gas cost and the
    floor data gas cost.

    Since at least one of the cases requires some execution gas expenditure
    (SSTORE clearing), we need to introduce an increment of the floor data cost
    above the transaction intrinsic gas cost, otherwise the floor data cost
    would always be the below the execution gas cost even after the refund is
    applied.

    On EIP-8037 the SSTORE schedule is higher and existing-authority auths add
    top-frame ``AUTH_BASE`` state gas, so the delta must cover those too.
    """
    if not fork.is_eip_enabled(8037):
        return 250
    # Floor is searched as ~intrinsic + delta. Post-refund cost at
    # prefix-only (+ top-frame) consumption is at most
    # intrinsic + top_frame + prefix (when refund is zero) and still
    # above intrinsic + (top_frame + prefix) * 4/5 when the EIP-3529
    # cap binds. Cover the no-refund upper bound so all three
    # refund-vs-floor cases remain reachable.
    return top_frame_execution + top_frame_state + prefix_code_gas + 500


@pytest.fixture
def execution_gas_used(
    tx_intrinsic_gas_cost_before_execution: int,
    tx_floor_data_cost: int,
    max_refund: int,
    prefix_code_gas: int,
    top_frame_execution: int,
    top_frame_state: int,
    refund_test_type: RefundTestType,
) -> int:
    """
    Return the amount of gas that needs to be consumed by the execution.

    This gas amount is on top of the transaction intrinsic gas cost (and, on
    EIP-8037, on top of the authorization top-frame charge).

    If this value were zero it would result in the refund being applied to the
    execution gas cost and the resulting amount being always below the floor
    data cost, hence we need to find a higher value in this function to ensure
    we get both scenarios where the refund drives the execution cost below the
    floor data cost and above the floor data cost.
    """

    def execution_gas_cost(execution_gas: int) -> int:
        total_gas_used = (
            tx_intrinsic_gas_cost_before_execution
            + top_frame_execution
            + top_frame_state
            + execution_gas
        )
        capped_refund = min(max_refund, total_gas_used // 5)
        return total_gas_used - capped_refund

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
    top_frame_execution: int,
    top_frame_state: int,
) -> int:
    """Return the refund gas of the transaction."""
    total_gas_used = (
        tx_intrinsic_gas_cost_before_execution
        + top_frame_execution
        + top_frame_state
        + execution_gas_used
    )
    return min(max_refund, total_gas_used // 5)


@pytest.fixture
def to(
    fork: Fork,
    pre: Alloc,
    execution_gas_used: int,
    prefix_code: Bytecode,
    prefix_code_gas: int,
    code_storage: Dict,
) -> Address | None:
    """Return a contract that consumes the expected execution gas."""
    code = (
        prefix_code
        + GasConsumer(gas=execution_gas_used - prefix_code_gas, fork=fork)
        + Op.STOP
    )
    return pre.deploy_contract(code, storage=code_storage)


@pytest.fixture
def tx_gas_limit(
    tx_intrinsic_gas_cost_including_floor_data_cost: int,
    tx_intrinsic_gas_cost_before_execution: int,
    execution_gas_used: int,
    top_frame_execution: int,
    top_frame_state: int,
) -> int:
    """
    Gas limit for the transaction.

    Sized to the exact pre-refund consumption when that already clears the
    EIP-7623 floor. When consumption sits below the floor (refund-free
    LESS_THAN cases on EIP-8037), bump the limit up to the floor so the
    transaction remains intrinsically valid while settlement still sees
    the lower consumed amount.
    """
    consumed = (
        tx_intrinsic_gas_cost_before_execution
        + top_frame_execution
        + top_frame_state
        + execution_gas_used
    )
    return max(consumed, tx_intrinsic_gas_cost_including_floor_data_cost)


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
def test_gas_refunds_from_data_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    tx: Transaction,
    tx_floor_data_cost: int,
    tx_intrinsic_gas_cost_before_execution: int,
    execution_gas_used: int,
    refund: int,
    top_frame_execution: int,
    top_frame_state: int,
    refund_test_type: RefundTestType,
) -> None:
    """
    Test gas refunds deducted from the execution gas cost and not the data
    floor.

    Pre-EIP-8037: existing-authority auth refunds flow through
    ``refund_counter`` (EIP-3529 1/5 cap) together with storage-clear refunds.

    EIP-8037 / EIP-2780: existing-authority auths pay top-frame ``AUTH_BASE``
    with no auth refund; only storage-clear refunds remain in
    ``refund_counter``. Receipt ``cumulative_gas_used`` is the sum of
    intrinsic execution, top-frame execution/state, and EVM gas, minus the
    capped storage refund, then floored by EIP-7623.
    """
    gas_used = (
        tx_intrinsic_gas_cost_before_execution
        + top_frame_execution
        + top_frame_state
        + execution_gas_used
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
