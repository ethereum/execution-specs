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
    AuthorizationTuple,
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

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7778.md"
REFERENCE_SPEC_VERSION = "54fba02495a05b57acd3f27473d0493b40a9d920"


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
) -> Tuple[int, int, int, Transaction]:
    """Build a transaction that has different refund types from a fork."""
    # All essential calc functions
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_refund_quotient = fork.max_refund_quotient()
    gsc = fork.gas_costs()
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

    for refund_type in refund_types:
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

            case RefundTypes.AUTHORIZATION_EXISTING_AUTHORITY:
                code += Op.PUSH0
                delegated_contract = pre.deploy_contract(code=Bytecode())
                authorization_list = [
                    AuthorizationTuple(
                        address=delegated_contract,
                        nonce=0,
                        signer=pre.fund_eoa(amount=1),
                    )
                    for _ in range(refunds_count)
                ]
                refund_counter += (
                    gsc.REFUND_AUTH_PER_EXISTING_ACCOUNT * refunds_count
                )
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

    gas_used_pre_refund = intrinsic_cost_calc(
        calldata=call_data,
        return_cost_deducted_prior_execution=True,
        authorization_list_or_count=authorization_list,
    ) + code.gas_cost(fork)

    # Calculate refund (still applied to user's balance)
    if not refund_tx_reverts:
        refund_counter += code.refund(fork)

    effective_refund = min(
        refund_counter, gas_used_pre_refund // max_refund_quotient
    )
    gas_used_post_refund = gas_used_pre_refund - effective_refund
    call_data_floor_cost = data_floor_calc(data=call_data)

    refund_tx_block_gas_used = max(call_data_floor_cost, gas_used_pre_refund)
    refund_tx_gas_used = max(call_data_floor_cost, gas_used_post_refund)

    # Build refund transaction
    refund_tx = Transaction(
        to=contract_address,
        data=call_data,
        gas_limit=refund_tx_block_gas_used + refund_tx_extra_gas,
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

    return (
        gas_used_post_refund,
        gas_used_pre_refund,
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
@pytest.mark.valid_from("Amsterdam")
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

    (_, gas_used_pre_refund, call_data_floor_cost, refund_tx) = (
        build_refund_tx(
            fork=fork,
            pre=pre,
            post=post,
            refund_types={refund_type},
            refunds_count=refunds_count,
            refund_tx_reverts=refund_tx_reverts,
        )
    )

    refund_tx_block_gas_used = max(gas_used_pre_refund, call_data_floor_cost)

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
@pytest.mark.valid_from("Amsterdam")
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

    refunds_count = 10
    stop_bytecode = Op.STOP
    stop_address = pre.deterministic_deploy_contract(deploy_code=stop_bytecode)

    post = Alloc()
    (
        gas_used_post_refund,
        gas_used_pre_refund,
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
    refund_tx_block_gas_used = max(gas_used_pre_refund, call_data_floor_cost)

    extra_tx_sender = pre.fund_eoa()
    extra_tx_calldata = b"\xff" if extra_tx_data_floor else b""
    extra_tx_intrinsic_gas_cost = intrinsic_cost_calc(
        calldata=extra_tx_calldata
    )

    extra_tx = Transaction(
        to=stop_address,
        data=extra_tx_calldata,
        gas_limit=extra_tx_intrinsic_gas_cost,
        sender=extra_tx_sender,
        expected_receipt={
            "gas_used": refund_tx_gas_used + extra_tx_intrinsic_gas_cost,
        },
        error=TransactionException.GAS_ALLOWANCE_EXCEEDED
        if exceed_block_gas_limit
        else None,
    )

    total_block_gas_used = (
        refund_tx_block_gas_used + extra_tx_intrinsic_gas_cost
    )
    if exceed_block_gas_limit:
        environment_gas_limit = total_block_gas_used - 1
    else:
        environment_gas_limit = total_block_gas_used

    txs = [refund_tx, extra_tx]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=BlockException.GAS_USED_OVERFLOW
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
@pytest.mark.valid_from("Amsterdam")
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
    if refund_type == RefundTypes.STORAGE_CLEAR:
        if (
            refund_tx_reverts
            and calldata_test_type
            == CallDataTestType.DATA_FLOOR_BETWEEN_TX_GAS_BEFORE_AND_AFTER
        ):
            pytest.skip(
                "calldata_cost cannot be between pre and post refund gas"
                "since refund is zero when execution reverts"
            )

    match refund_type:
        case RefundTypes.STORAGE_CLEAR:
            bytes_to_add_per_iteration = b"00" * 2
        case RefundTypes.AUTHORIZATION_EXISTING_AUTHORITY:
            bytes_to_add_per_iteration = b"00" * 10
        case _:
            raise ValueError(
                f"Unknown refund type: {refund_type} (Test needs update)"
            )

    data = b""

    # Time to start searching for appropriate call data for each scenario
    num_iterations = 200
    # Currently in Amsterdam, the optimal call data is found in about
    # 30 iterations for CallDataTestType.DATA_FLOOR_GT_TX_GAS_BEFORE_REFUND.
    # Setting this higher just to make it
    # a bit more future proof if the gas calc logic changes
    found_call_data = False
    for _ in range(num_iterations):
        post = Alloc()

        (
            gas_used_post_refund,
            gas_used_pre_refund,
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

    refund_tx_block_gas_used = max(call_data_floor_cost, gas_used_pre_refund)

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

    (_, gas_used_pre_refund, call_data_floor_cost, refund_tx) = (
        build_refund_tx(
            fork=fork,
            pre=pre,
            post=post,
            refund_types=refund_types,
            refunds_count=refunds_count,
            refund_tx_reverts=refund_tx_reverts,
        )
    )

    refund_tx_block_gas_used = max(gas_used_pre_refund, call_data_floor_cost)

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
