"""
Test cases for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).
"""

from enum import Enum
from typing import Set, Tuple

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    Environment,
    Fork,
    RefundTypes,
    Transaction,
    TransactionException,
)
from execution_testing.base_types import HashInt
from execution_testing.vm import Op

from .spec import ref_spec_7778

REFERENCE_SPEC_GIT_PATH = ref_spec_7778.git_path
REFERENCE_SPEC_VERSION = ref_spec_7778.version


def build_refund_tx(
    fork: Fork,
    pre: Alloc,
    post: Alloc,
    refund_types: Set[RefundTypes],
    refunds_count: int = 1,
    refund_tx_reverts: bool = False,
    call_data: bytes = b"",
    refund_tx_has_extra_gas_limit: bool = False,
    exceed_block_gas_limit: bool = False,
) -> Tuple[int, int, int, int, Transaction]:
    """Build a transaction that has different refund types from a fork."""
    # All essential calc functions
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_refund_quotient = fork.max_refund_quotient()
    data_floor_calc = fork.transaction_data_floor_cost_calculator()

    # Initial account pre loading
    initial_fund = 10**18
    refund_tx_sender = pre.fund_eoa(initial_fund)

    # Initialize other aspects of pre-alloc
    code = Bytecode()
    authorization_list = None
    refund_counter = 0
    storage_slots = list(range(HashInt(refunds_count)))

    empty_storage_on_success = False
    refund_tx_extra_gas = 1 if refund_tx_has_extra_gas_limit else 0

    # Sort by name so iteration order is deterministic across Python
    # invocations (set iteration over enum members depends on Python's
    # per-process hash randomization).
    for refund_type in sorted(refund_types, key=lambda r: r.name):
        match refund_type:
            case RefundTypes.STORAGE_CLEAR:
                for slot in storage_slots:
                    code += Op.SSTORE(
                        slot,
                        Op.PUSH0,
                        # Gas accounting
                        original_value=1,
                        new_value=0,
                    )
                empty_storage_on_success = True

            case _:
                raise ValueError(
                    f"Unknown refund type: {refund_type} (Test needs update)"
                )

    if refund_tx_reverts:
        code += Op.REVERT(0, 0)

    contract_address = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(storage_slots, 1),
    )

    # Combined gas (execution + state) from intrinsic cost calculator
    combined_gas_used = intrinsic_cost_calc(
        calldata=call_data,
        return_cost_deducted_prior_execution=True,
        authorization_list_or_count=authorization_list,
    ) + code.gas_cost(fork)

    # EIP-8037: block gas_used only counts execution gas
    gas_used_pre_refund = combined_gas_used

    # Calculate refund (still applied to user's balance)
    if not refund_tx_reverts:
        refund_counter += code.refund(fork)

    # EIP-2780 moved the EIP-7702 authorization charge to the top frame,
    # so no transaction-level state gas remains here; the STORAGE_CLEAR
    # path carries none.
    remaining_state_gas = 0

    # In the spec, the refund cap uses tx_gas_used_before_refund which is
    # tx.gas - gas_left - state_gas_left (combined execution + remaining
    # state).
    combined_before_refund = gas_used_pre_refund + remaining_state_gas

    effective_refund = min(
        refund_counter, combined_before_refund // max_refund_quotient
    )
    receipt_gas_used = combined_before_refund - effective_refund
    call_data_floor_cost = data_floor_calc(data=call_data)

    # gas_used_post_refund is the "combined after refund" value used for
    # calldata floor comparisons and balance computation
    gas_used_post_refund = receipt_gas_used
    refund_tx_gas_used = max(call_data_floor_cost, gas_used_post_refund)

    # gas_limit must cover combined gas (execution + state)
    refund_tx_gas_limit = (
        max(call_data_floor_cost, combined_gas_used) + refund_tx_extra_gas
    )

    # Build refund transaction
    refund_tx = Transaction(
        to=contract_address,
        data=call_data,
        gas_limit=refund_tx_gas_limit,
        sender=refund_tx_sender,
        authorization_list=authorization_list,
        expected_receipt={
            "gas_used": refund_tx_gas_used,
        },
    )
    refund_tx_gas_price = (
        refund_tx.gas_price
        if refund_tx.gas_price
        else refund_tx.max_fee_per_gas
    )

    if (
        refund_tx_reverts
        or exceed_block_gas_limit
        or not empty_storage_on_success
    ):
        post[contract_address] = Account(
            storage=dict.fromkeys(storage_slots, 1),
        )
    else:
        post[contract_address] = Account(
            storage=dict.fromkeys(storage_slots, 0),
        )

    assert refund_tx_gas_price is not None, (
        "refund_tx_gas_price should not be None"
    )
    expected_balance = initial_fund - (
        refund_tx_gas_used * refund_tx_gas_price
    )

    if not exceed_block_gas_limit:
        post[refund_tx_sender] = Account(balance=expected_balance)

    # No transaction-level state gas is tracked here anymore; the third
    # element is always zero and kept for the return-tuple shape callers
    # unpack.
    return (
        receipt_gas_used,
        gas_used_pre_refund,
        remaining_state_gas,
        call_data_floor_cost,
        refund_tx,
    )


@pytest.mark.parametrize(
    "refund_tx_reverts",
    [
        pytest.param(True, id="refund_tx_reverts"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.with_all_refund_types()
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
@pytest.mark.valid_from("EIP8037")
def test_simple_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_reverts: bool,
) -> None:
    """Test gas accounting for all refund types available in the given fork."""
    refunds_count = 10

    post = Alloc()

    (
        _,
        gas_used_pre_refund,
        tx_state_gas,
        call_data_floor_cost,
        refund_tx,
    ) = build_refund_tx(
        fork=fork,
        pre=pre,
        post=post,
        refund_types={refund_type},
        refunds_count=refunds_count,
        refund_tx_reverts=refund_tx_reverts,
    )

    # EIP-8037: block gas_used = max(block_execution_gas, block_state_gas),
    # with the calldata floor binding the execution dimension.
    block_execution = max(gas_used_pre_refund, call_data_floor_cost)
    refund_tx_block_gas_used = max(block_execution, tx_state_gas)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx_block_gas_used,
            )
        ],
        post=post,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "refund_tx_reverts",
    [
        pytest.param(True, id="refund_tx_reverts"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.parametrize(
    "refund_tx_has_extra_gas_limit",
    [
        pytest.param(True, id="refund_tx_has_extra_gas"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.parametrize(
    "extra_tx_data_floor",
    [
        pytest.param(True, id=""),
        pytest.param(False, id="extra_tx_hits_data_floor"),
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
@pytest.mark.valid_from("EIP8037")
def test_multi_transaction_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_has_extra_gas_limit: bool,
    exceed_block_gas_limit: bool,
    extra_tx_data_floor: bool,
    refund_tx_reverts: bool,
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

    post = Alloc()
    (
        gas_used_post_refund,
        gas_used_pre_refund,
        tx_state_gas,
        call_data_floor_cost,
        refund_tx,
    ) = build_refund_tx(
        fork=fork,
        pre=pre,
        post=post,
        refund_types={refund_type},
        refunds_count=refunds_count,
        refund_tx_reverts=refund_tx_reverts,
        call_data=b"",
        refund_tx_has_extra_gas_limit=refund_tx_has_extra_gas_limit,
        exceed_block_gas_limit=exceed_block_gas_limit,
    )
    refund_tx_gas_used = max(gas_used_post_refund, call_data_floor_cost)

    extra_tx_sender = pre.fund_eoa()
    extra_tx_calldata = b"\xff" if extra_tx_data_floor else b""
    extra_tx_intrinsic_gas_cost = intrinsic_cost_calc(
        calldata=extra_tx_calldata
    )
    # Block execution gas applies the calldata floor to the actual charge.
    extra_tx_block_gas = max(
        intrinsic_cost_calc(
            calldata=extra_tx_calldata,
            return_cost_deducted_prior_execution=True,
        ),
        data_floor_calc(data=extra_tx_calldata),
    )

    extra_tx = Transaction(
        to=stop_address,
        data=extra_tx_calldata,
        gas_limit=extra_tx_intrinsic_gas_cost,
        sender=extra_tx_sender,
        expected_receipt={
            "gas_used": refund_tx_gas_used + extra_tx_intrinsic_gas_cost,
        },
        error=(
            TransactionException.GAS_ALLOWANCE_EXCEEDED
            if exceed_block_gas_limit
            else None
        ),
    )

    # EIP-8037: block_gas_used = max(sum_execution, sum_state)
    # Extra tx has no state gas, so its state gas contribution = 0
    block_execution = gas_used_pre_refund + extra_tx_block_gas
    block_state = tx_state_gas
    total_block_gas_used = max(block_execution, block_state)
    # The block gas_limit must accommodate extra_tx's full gas_limit
    # (floor-inclusive, like its block-execution charge). For
    # exceed_block_gas_limit=True we set the limit below
    # total_block_gas_used to test that the extra_tx fails.
    if exceed_block_gas_limit:
        environment_gas_limit = total_block_gas_used - 1
    else:
        environment_gas_limit = (
            gas_used_pre_refund + extra_tx_intrinsic_gas_cost
        )

    txs = [refund_tx, extra_tx]

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


@pytest.mark.parametrize(
    "refund_tx_reverts",
    [
        pytest.param(True, id="refund_tx_reverts"),
        pytest.param(False, id=""),
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
    lambda refund_type, refund_tx_reverts, calldata_test_type, **_: not (
        refund_type == RefundTypes.STORAGE_CLEAR
        and refund_tx_reverts
        and calldata_test_type
        == CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER
    ),
    reason=(
        "STORAGE_CLEAR refund is zero on revert, so the (post, pre) "
        "interval that DATA_FLOOR_BETWEEN needs is empty"
    ),
)
@pytest.mark.valid_from("EIP8037")
def test_varying_calldata_costs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_reverts: bool,
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
    for _ in range(num_iterations):
        post = Alloc()

        (
            gas_used_post_refund,
            gas_used_pre_refund,
            tx_state_gas,
            call_data_floor_cost,
            refund_tx,
        ) = build_refund_tx(
            fork=fork,
            pre=pre,
            post=post,
            refund_types={refund_type},
            refund_tx_reverts=refund_tx_reverts,
            call_data=data,
        )

        if (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_LT_TX_GAS_AFTER_REFUND
        ):
            if call_data_floor_cost < gas_used_post_refund:
                found_call_data = True
                break
        elif (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER
        ):
            if (
                gas_used_post_refund
                < call_data_floor_cost
                < gas_used_pre_refund
            ):
                found_call_data = True
                break
        elif (
            calldata_test_type
            == CallDataTestType.DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND
        ):
            if gas_used_pre_refund < call_data_floor_cost:
                found_call_data = True
                break
        else:
            raise ValueError("Invalid calldata test type")

        data += bytes_to_add_per_iteration

    if not found_call_data:
        raise ValueError(
            f"Could not find the call_data with {num_iterations} iterations."
        )

    # EIP-8037: block gas_used = max(block_execution_gas, block_state_gas),
    # with the calldata floor binding the execution dimension.
    block_execution = max(gas_used_pre_refund, call_data_floor_cost)
    refund_tx_block_gas_used = max(block_execution, tx_state_gas)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx_block_gas_used,
            )
        ],
        post=post,
    )


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "refund_tx_reverts",
    [
        pytest.param(True, id="refund_tx_reverts"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.with_all_refund_types()
@pytest.mark.filter_combinations(
    lambda refund_type, refund_tx_reverts, **_: not (
        refund_type == RefundTypes.STORAGE_CLEAR and refund_tx_reverts
    ),
    reason=(
        "STORAGE_CLEAR refund is zero on revert, so post_refund == "
        "pre_refund and the admission bypass cannot manifest"
    ),
)
@pytest.mark.exception_test
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
@pytest.mark.valid_from("EIP7778")
def test_extra_tx_admission_uses_pre_refund_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_type: RefundTypes,
    refund_tx_reverts: bool,
) -> None:
    """
    Test that the admission gate uses the pre-refund accumulator when
    the trailing tx's gas_limit exceeds its actual usage.

    Without this slack a post-refund gate is masked: the block is
    still rejected by the gas_used > gas_limit check. With it, a buggy
    implementation admits the extra tx yet stays within the block gas
    limit, diverging from the expected-invalid fixture.
    """
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()

    refunds_count = 10
    stop_address = pre.deterministic_deploy_contract(deploy_code=Op.STOP)

    post = Alloc()
    (
        gas_used_post_refund,
        gas_used_pre_refund,
        _,
        call_data_floor_cost,
        refund_tx,
    ) = build_refund_tx(
        fork=fork,
        pre=pre,
        post=post,
        refund_types={refund_type},
        refunds_count=refunds_count,
        refund_tx_reverts=refund_tx_reverts,
        exceed_block_gas_limit=True,
    )

    assert gas_used_pre_refund > gas_used_post_refund, (
        "Parametrization must produce a refund; without one the admission "
        "bypass cannot occur"
    )

    refund_tx_block_gas_used = max(gas_used_pre_refund, call_data_floor_cost)

    extra_tx_sender = pre.fund_eoa()
    extra_tx_intrinsic = intrinsic_cost_calc(calldata=b"")

    # Slack so a buggy admit stays within the block gas limit.
    extra_tx_gas_limit = 2 * extra_tx_intrinsic
    extra_tx = Transaction(
        to=stop_address,
        gas_limit=extra_tx_gas_limit,
        sender=extra_tx_sender,
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
    )

    environment_gas_limit = refund_tx_block_gas_used + extra_tx_gas_limit - 1

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx, extra_tx],
                exception=[
                    BlockException.GAS_USED_OVERFLOW,
                    TransactionException.GAS_ALLOWANCE_EXCEEDED,
                ],
                gas_limit=environment_gas_limit,
            )
        ],
        post=post,
        genesis_environment=Environment(gas_limit=environment_gas_limit),
    )


@pytest.mark.parametrize(
    "refund_tx_reverts",
    [
        pytest.param(True, id="refund_tx_reverts"),
        pytest.param(False, id=""),
    ],
)
@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
@pytest.mark.valid_from("Amsterdam")
def test_multiple_refund_types_in_one_tx(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    refund_tx_reverts: bool,
) -> None:
    """Test gas accounting for all refund types available in the given fork."""
    refunds_count = 10

    post = Alloc()
    refund_types = set(fork.refund_types())

    (
        _,
        gas_used_pre_refund,
        tx_state_gas,
        call_data_floor_cost,
        refund_tx,
    ) = build_refund_tx(
        fork=fork,
        pre=pre,
        post=post,
        refund_types=refund_types,
        refunds_count=refunds_count,
        refund_tx_reverts=refund_tx_reverts,
    )

    # EIP-8037: block gas_used = max(block_execution_gas, block_state_gas),
    # with the calldata floor binding the execution dimension.
    block_execution = max(gas_used_pre_refund, call_data_floor_cost)
    refund_tx_block_gas_used = max(block_execution, tx_state_gas)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=refund_tx_block_gas_used,
            )
        ],
        post=post,
    )


@pytest.mark.execute(pytest.mark.skip(reason="Requires specific gas price"))
@pytest.mark.valid_from("EIP8037")
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
        tx1_pre_refund - Op.SSTORE(new_value=1).state_cost(fork), tx1_floor
    )
    tx1 = Transaction(
        to=tx1_target,
        gas_limit=tx1_contribution,
        sender=tx1_sender,
        data=tx1_data,
        # TODO: gas_used in expected_receipt is ignored by
        # verify_transaction_receipt; only cumulative_gas_used is
        # checked. To be fixed by #2855.
        expected_receipt={"gas_used": tx1_contribution},
    )
    tx1_gas_price = tx1.gas_price if tx1.gas_price else tx1.max_fee_per_gas
    assert tx1_gas_price is not None
    post[tx1_target] = Account(storage={0: 1})
    post[tx1_sender] = Account(
        balance=initial_fund - tx1_contribution * tx1_gas_price
    )

    # tx2: SSTORE-clear with normal refund, refund not clipped to floor.
    (
        tx2_post_refund,
        tx2_pre_refund,
        _,
        tx2_floor,
        tx2,
    ) = build_refund_tx(
        fork=fork,
        pre=pre,
        post=post,
        refund_types={RefundTypes.STORAGE_CLEAR},
        refunds_count=10,
    )
    assert tx2_pre_refund > tx2_floor, "tx2: pre_refund must exceed floor"
    assert tx2_post_refund > tx2_floor, (
        "tx2: refund must not be clipped to floor"
    )
    tx2_contribution = max(tx2_pre_refund, tx2_floor)

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
        # TODO: gas_used in expected_receipt is ignored by
        # verify_transaction_receipt; only cumulative_gas_used is
        # checked. To be fixed by #2855.
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
