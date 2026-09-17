"""
Test cases for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).
"""

from enum import Enum

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    EIPChecklist,
    Environment,
    Fork,
    RefundTypes,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

from .helpers import RefundTransaction, TransactionFailure
from .spec import ref_spec_7778

REFERENCE_SPEC_GIT_PATH = ref_spec_7778.git_path
REFERENCE_SPEC_VERSION = ref_spec_7778.version


INITIAL_FUND = 10**18

pytestmark = [pytest.mark.valid_from("EIP7778")]


@EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable()
@EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable.Revert()
@EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable.UpperRevert()
@EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable.OutOfGas()
@EIPChecklist.GasRefundsChanges.Test.ExceptionalAbort.Revertable.InvalidOpcode()
@TransactionFailure.with_all_tx_failures()
@pytest.mark.with_all_refund_types()
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
def test_simple_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_failure: TransactionFailure | None,
) -> None:
    """Test gas accounting for all refund types available in the given fork."""
    refunds_count = 10

    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=refunds_count,
        tx_failure=refund_tx_failure,
    )

    refund_tx.set_pre(pre)
    post = refund_tx.post(pre)

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        # The refund reaches the sender's balance even though it stays
        # out of the block's gas accounting.
        sender_post = post[refund_tx.sender]
        assert sender_post is not None, "RefundTransaction.post sets it"
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                refund_tx.sender: BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=sender_post.balance,
                        )
                    ],
                ),
            }
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx.block_gas_used(),
                expected_block_access_list=expected_block_access_list,
            )
        ],
        post=post,
    )


@EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Over()
@pytest.mark.inclusion_test
@TransactionFailure.with_all_tx_failures()
@pytest.mark.parametrize(
    "refund_tx_has_gas_limit_slack",
    [
        pytest.param(True, id="refund_tx_has_gas_limit_slack"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.parametrize(
    "trailing_tx_data_floor",
    [
        pytest.param(True, id="trailing_tx_hits_data_floor"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        False,
    ],
)
@pytest.mark.with_all_refund_types()
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
def test_multi_transaction_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_has_gas_limit_slack: bool,
    exceed_block_gas_limit: bool,
    trailing_tx_data_floor: bool,
    refund_tx_failure: TransactionFailure | None,
) -> None:
    """
    Test block gas accounting with refunds per EIP-7778.

    When exceed_block_gas_limit=True, we create a scenario where:
    - Pre-refund gas (gas_used) > block_gas_limit - intrinsic_cost
      (no room for another tx with correct EIP-7778 accounting)
    - Post-refund gas (gas_spent) <= block_gas_limit - intrinsic_cost
      (appears to have room with old refund-based accounting)

    This tests that clients correctly use pre-refund gas for block accounting.
    """
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    data_floor_calc = fork.transaction_data_floor_cost_calculator()

    refunds_count = 10
    stop_bytecode = Op.STOP
    stop_address = pre.deterministic_deploy_contract(deploy_code=stop_bytecode)

    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=refunds_count,
        tx_failure=refund_tx_failure,
        refund_tx_has_gas_limit_slack=refund_tx_has_gas_limit_slack,
    )
    refund_tx.set_pre(pre)
    post = refund_tx.post(pre, block_is_invalid=exceed_block_gas_limit)
    trailing_tx_sender = pre.fund_eoa()
    trailing_tx_calldata = b"\xff" if trailing_tx_data_floor else b""
    trailing_tx_intrinsic_gas_cost = intrinsic_cost_calc(
        calldata=trailing_tx_calldata
    )
    # Block execution gas applies the calldata floor to the actual charge.
    trailing_tx_block_gas = max(
        intrinsic_cost_calc(
            calldata=trailing_tx_calldata,
            return_cost_deducted_prior_execution=True,
        ),
        data_floor_calc(data=trailing_tx_calldata),
    )

    trailing_tx = Transaction(
        to=stop_address,
        data=trailing_tx_calldata,
        gas_limit=trailing_tx_intrinsic_gas_cost,
        sender=trailing_tx_sender,
        expected_receipt={
            "gas_used": trailing_tx_intrinsic_gas_cost,
        },
        error=(
            TransactionException.GAS_ALLOWANCE_EXCEEDED
            if exceed_block_gas_limit
            else None
        ),
    )

    # Extra tx has no state gas, so its state gas contribution = 0
    block_execution = refund_tx.gas_used_pre_refund + trailing_tx_block_gas
    block_state = refund_tx.state_gas
    total_block_gas_used = max(block_execution, block_state)
    # The block gas_limit must accommodate trailing_tx's full gas_limit
    # (floor-inclusive, like its block-execution charge). For
    # exceed_block_gas_limit=True we set the limit below
    # total_block_gas_used to test that the trailing_tx fails.
    if exceed_block_gas_limit:
        environment_gas_limit = total_block_gas_used - 1
    else:
        environment_gas_limit = (
            refund_tx.gas_used_pre_refund + trailing_tx_intrinsic_gas_cost
        )

    txs = [refund_tx, trailing_tx]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=[
                    BlockException.GAS_USED_OVERFLOW,
                    TransactionException.GAS_ALLOWANCE_EXCEEDED,
                ]
                if exceed_block_gas_limit
                else None,
                expected_gas_used=total_block_gas_used
                if not exceed_block_gas_limit
                else None,
                gas_limit=environment_gas_limit,
            )
        ],
        post=post,
        genesis_environment=Environment(gas_limit=environment_gas_limit),
    )


class CallDataTestType(Enum):
    """Refund test type."""

    DATA_FLOOR_LT_TX_GAS_AFTER_REFUND = -1
    """
    calldata_floor < tx_gas_after_refund.
    """
    DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER = 0
    """
    tx_gas_after_refund < calldata_floor < tx_gas_before_refund.
    """
    DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND = 1
    """calldata_floor > tx_gas_before_refund."""


@EIPChecklist.GasRefundsChanges.Test.CrossFunctional.CalldataCost()
@pytest.mark.parametrize(
    "refund_tx_failure",
    [
        pytest.param(TransactionFailure.REVERT, id="refund_tx_reverts"),
        pytest.param(None, id=""),
    ],
)
@pytest.mark.parametrize(
    "calldata_test_type",
    [
        CallDataTestType.DATA_FLOOR_LT_TX_GAS_AFTER_REFUND,
        CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER,
        CallDataTestType.DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND,
    ],
)
@pytest.mark.with_all_refund_types()
@pytest.mark.filter_combinations(
    lambda refund_type, refund_tx_failure, calldata_test_type, **_: not (
        refund_type == RefundTypes.STORAGE_CLEAR
        and refund_tx_failure is not None
        and calldata_test_type
        == CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER
    ),
    reason=(
        "STORAGE_CLEAR refund is zero on revert, so the (post, pre) "
        "interval that DATA_FLOOR_BETWEEN needs is empty"
    ),
)
def test_varying_calldata_costs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_failure: TransactionFailure | None,
    calldata_test_type: CallDataTestType,
) -> None:
    """
    Test by varying the calldata_floor_cost.

    Performs tests for the following 3 scenarios.

    1. calldata_floor < tx_gas_after_refund
    2. tx_gas_after_refund < calldata_floor < tx_gas_before_refund
    3. calldata_floor > tx_gas_before_refund
    """
    match refund_type:
        case RefundTypes.STORAGE_CLEAR:
            bytes_to_add_per_iteration = b"00" * 2
        case _:
            raise ValueError(
                f"Unknown refund type: {refund_type} (Test needs update)"
            )

    data = b""

    # Time to start searching for appropriate call data for each scenario
    num_iterations = 200
    # Currently in EIP-7778, the optimal call data is found in about
    # 30 iterations for CallDataTestType.DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND.
    # Setting this higher just to make it
    # a bit more future proof if the gas calc logic changes
    found_call_data = False
    refund_tx: RefundTransaction | None = None
    for _ in range(num_iterations):
        refund_tx = RefundTransaction.build(
            fork=fork,
            sender=pre.fund_eoa(INITIAL_FUND),
            refund_types={refund_type},
            tx_failure=refund_tx_failure,
            call_data=data,
        )

        if (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_LT_TX_GAS_AFTER_REFUND
        ):
            if refund_tx.call_data_floor_cost < refund_tx.receipt_gas_used:
                found_call_data = True
                break
        elif (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER
        ):
            if (
                refund_tx.receipt_gas_used
                < refund_tx.call_data_floor_cost
                < refund_tx.gas_used_pre_refund
            ):
                found_call_data = True
                break
        elif (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND
        ):
            if refund_tx.gas_used_pre_refund < refund_tx.call_data_floor_cost:
                found_call_data = True
                break
        else:
            raise ValueError("Invalid calldata test type")

        data += bytes_to_add_per_iteration

    if not found_call_data or refund_tx is None:
        raise ValueError(
            f"Could not find the call_data with {num_iterations} iterations."
        )

    refund_tx.set_pre(pre)
    post = refund_tx.post(pre)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx.block_gas_used(),
            )
        ],
        post=post,
    )


@EIPChecklist.BlockLevelConstraint.Test.Boundary.Under()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Exact()
@EIPChecklist.BlockLevelConstraint.Test.Boundary.Over()
@pytest.mark.inclusion_test
@TransactionFailure.with_all_tx_failures()
@pytest.mark.with_all_refund_types()
@pytest.mark.filter_combinations(
    lambda refund_type, refund_tx_failure, **_: not (
        refund_type == RefundTypes.STORAGE_CLEAR
        and refund_tx_failure is not None
    ),
    reason=(
        "STORAGE_CLEAR refund is zero on revert, so post_refund == "
        "pre_refund and the admission bypass cannot manifest"
    ),
)
@pytest.mark.parametrize(
    "trailing_tx_block_gas_limit_delta",
    [
        pytest.param(
            1,
            id="extra_block_gas_limit",
        ),
        pytest.param(
            0,
            id="exact_block_gas_limit",
        ),
        pytest.param(
            -1,
            marks=[pytest.mark.exception_test],
            id="exceeds_block_gas_limit",
        ),
    ],
)
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
def test_trailing_tx_admission_uses_pre_refund_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_failure: TransactionFailure | None,
    trailing_tx_block_gas_limit_delta: int,
) -> None:
    """
    Test that the admission gate uses the pre-refund accumulator when
    the trailing tx's gas_limit exceeds its actual usage.

    Without this slack a post-refund gate is masked: the block is
    still rejected by the gas_used > gas_limit check. With it, a buggy
    implementation admits the trailing tx yet stays within the block gas
    limit, diverging from the expected-invalid fixture.
    """
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()

    refunds_count = 10
    stop_address = pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    exceeds_block_gas_limit = trailing_tx_block_gas_limit_delta < 0

    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={refund_type},
        refunds_count=refunds_count,
        tx_failure=refund_tx_failure,
    )
    refund_tx.set_pre(pre)

    assert refund_tx.gas_used_pre_refund > refund_tx.receipt_gas_used, (
        "Parametrization must produce a refund; without one the admission "
        "bypass cannot occur"
    )

    refund_tx_block_gas_used = refund_tx.block_execution()

    trailing_tx_sender = pre.fund_eoa()
    trailing_tx_intrinsic_gas_cost = intrinsic_cost_calc(calldata=b"")

    # Slack so a buggy admit stays within the block gas limit.
    trailing_tx_gas_limit = 2 * trailing_tx_intrinsic_gas_cost
    trailing_tx = Transaction(
        to=stop_address,
        gas_limit=trailing_tx_gas_limit,
        sender=trailing_tx_sender,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if exceeds_block_gas_limit
        else None,
    )

    environment_gas_limit = (
        refund_tx_block_gas_used
        + trailing_tx_gas_limit
        + trailing_tx_block_gas_limit_delta
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx, trailing_tx],
                exception=[
                    BlockException.GAS_USED_OVERFLOW,
                    TransactionException.GAS_ALLOWANCE_EXCEEDED,
                ]
                if exceeds_block_gas_limit
                else None,
                gas_limit=environment_gas_limit,
            )
        ],
        post=refund_tx.post(pre, exceeds_block_gas_limit),
        genesis_environment=Environment(gas_limit=environment_gas_limit),
    )


@TransactionFailure.with_all_tx_failures()
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
def test_multiple_refund_types_in_one_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_tx_failure: TransactionFailure | None,
) -> None:
    """Test gas accounting for all refund types available in the given fork."""
    refunds_count = 10

    refund_types = set(fork.refund_types())

    refund_tx = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types=refund_types,
        refunds_count=refunds_count,
        tx_failure=refund_tx_failure,
    )
    refund_tx.set_pre(pre)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx.block_gas_used(),
            )
        ],
        post=refund_tx.post(pre),
    )


@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
def test_mixed_gas_regimes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Lock in block-level gas accounting across a block where each tx hits a
    different regime.

    tx1: SSTORE-set fresh slot (no refund, pre_refund > floor).
    tx2: SSTORE-clear x10 (normal refund, refund not clipped to floor).
    tx3: 1000 zero-byte calldata to STOP (floor binds fee and block gas).

    The floor binds the tx-level fee (tx_gas_used = max(post_refund,
    floor)) and the block's execution dimension (max(pre_refund gas minus
    state gas, floor)) alike. Per-tx sender balance is also asserted to
    lock in that the floor-binding tx pays `floor * gas_price`, not
    `pre_refund * gas_price`.
    """
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    data_floor_calc = fork.transaction_data_floor_cost_calculator()
    initial_fund = 10**18

    post = Alloc()

    # tx1: SSTORE-set to a fresh slot. No refund.
    tx1_code = Op.SSTORE(0, 1, original_value=0, new_value=1)
    tx1_target = pre.deploy_contract(code=tx1_code)
    tx1_sender = pre.fund_eoa(initial_fund)
    tx1_data = b""
    # Full intrinsic + execution gas (execution + state) sizes the gas limit
    # and the balance charged to the sender.
    tx1_pre_refund = intrinsic_cost_calc(
        calldata=tx1_data,
        return_cost_deducted_prior_execution=True,
    ) + tx1_code.gas_cost(fork)
    tx1_floor = data_floor_calc(data=tx1_data)
    assert tx1_pre_refund > tx1_floor, "tx1: pre_refund must exceed floor"
    tx1_contribution = max(tx1_pre_refund, tx1_floor)
    # EIP-8037: block gas_used counts only execution gas; the SSTORE-set
    # state gas lives in the separate state dimension, so the block-level
    # contribution excludes it.
    tx1_block_contribution = max(
        tx1_pre_refund - tx1_code.state_cost(fork), tx1_floor
    )
    tx1 = Transaction(
        to=tx1_target,
        gas_limit=tx1_contribution,
        sender=tx1_sender,
        data=tx1_data,
        expected_receipt={"gas_used": tx1_contribution},
    )
    tx1_gas_price = tx1.gas_price if tx1.gas_price else tx1.max_fee_per_gas
    assert tx1_gas_price is not None
    post[tx1_target] = Account(storage={0: 1})
    post[tx1_sender] = Account(
        balance=initial_fund - tx1_contribution * tx1_gas_price
    )

    # tx2: SSTORE-clear with normal refund, refund not clipped to floor.
    tx2 = RefundTransaction.build(
        fork=fork,
        sender=pre.fund_eoa(INITIAL_FUND),
        refund_types={RefundTypes.STORAGE_CLEAR},
        refunds_count=10,
    )
    tx2.set_pre(pre)
    for addr, account in tx2.post(pre).items():
        post[addr] = account
    assert tx2.gas_used_pre_refund > tx2.call_data_floor_cost, (
        "tx2: pre_refund must exceed floor"
    )
    assert tx2.receipt_gas_used > tx2.call_data_floor_cost, (
        "tx2: refund must not be clipped to floor"
    )
    tx2_contribution = tx2.block_execution()

    # tx3: floor-binding via 1000 zero bytes of calldata to STOP.
    tx3_target = pre.deterministic_deploy_contract(deploy_code=Op.STOP)
    tx3_sender = pre.fund_eoa(initial_fund)
    tx3_data = b"\x00" * 1000
    tx3_pre_refund = intrinsic_cost_calc(
        calldata=tx3_data,
        return_cost_deducted_prior_execution=True,
    )
    tx3_floor = data_floor_calc(data=tx3_data)
    assert tx3_floor > tx3_pre_refund, "tx3: floor must bind upward"
    tx3_fee_gas = max(tx3_pre_refund, tx3_floor)
    # The floor binds the block's execution dimension as well as the fee.
    tx3_block_contribution = max(tx3_pre_refund, tx3_floor)
    tx3 = Transaction(
        to=tx3_target,
        gas_limit=tx3_fee_gas,
        sender=tx3_sender,
        data=tx3_data,
        expected_receipt={"gas_used": tx3_fee_gas},
    )
    tx3_gas_price = tx3.gas_price if tx3.gas_price else tx3.max_fee_per_gas
    assert tx3_gas_price is not None
    post[tx3_sender] = Account(
        balance=initial_fund - tx3_fee_gas * tx3_gas_price
    )

    total_gas_used = (
        tx1_block_contribution + tx2_contribution + tx3_block_contribution
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1, tx2, tx3],
                expected_gas_used=total_gas_used,
            )
        ],
        post=post,
    )
