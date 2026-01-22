"""
Test cases for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).
"""

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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7778.md"
REFERENCE_SPEC_VERSION = "54fba02495a05b57acd3f27473d0493b40a9d920"


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
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_refund_quotient = fork.max_refund_quotient()

    refunds_count = 10
    initial_fund = 10**18
    refund_tx_sender = pre.fund_eoa(initial_fund)

    post = {}

    match refund_type:
        case RefundTypes.STORAGE_CLEAR:
            storage_slots = list(range(refunds_count))

            code = Bytecode()
            for slot in storage_slots:
                code += Op.SSTORE(
                    slot,
                    Op.PUSH0,
                    # Gas accounting
                    original_value=1,
                    new_value=0,
                )
            if refund_tx_reverts:
                code += Op.REVERT(0, 0)

            contract_address = pre.deploy_contract(
                code=code,
                storage=dict.fromkeys(storage_slots, 1),
            )
            gas_used_pre_refund = intrinsic_cost_calc() + code.gas_cost(fork)

            # Calculate refund (still applied to user's balance)
            refund_counter = code.refund(fork)
            effective_refund = min(
                refund_counter, gas_used_pre_refund // max_refund_quotient
            )
            assert effective_refund > 0, (
                f"effective_refund ({effective_refund}) must be greater than 0"
            )
            gas_used_post_refund = gas_used_pre_refund - effective_refund
            refund_tx_gas_used = gas_used_pre_refund
            refund_tx_gas_spent = gas_used_post_refund

            if refund_tx_reverts:
                refund_tx_gas_spent = refund_tx_gas_used

            refund_tx = Transaction(
                to=contract_address,
                gas_limit=refund_tx_gas_used,
                sender=refund_tx_sender,
                expected_receipt={
                    "gas_used": refund_tx_gas_used,
                    "gas_spent": refund_tx_gas_spent,
                },
            )
            refund_tx_gas_price = refund_tx.gas_price

            if refund_tx_reverts:
                post[contract_address] = Account(
                    storage=dict.fromkeys(storage_slots, 1),
                )
            else:
                post[contract_address] = Account(
                    storage=dict.fromkeys(storage_slots, 0),
                )

        case RefundTypes.AUTHORIZATION_EXISTING_AUTHORITY:
            if refund_tx_reverts:
                code = Op.REVERT(0, 0)
            else:
                code = Op.STOP

            contract_address = pre.deterministic_deploy_contract(
                deploy_code=code
            )

            authorization_list = [
                AuthorizationTuple(
                    address=contract_address,
                    nonce=0,
                    signer=pre.fund_eoa(amount=1),
                )
                for _ in range(refunds_count)
            ]
            gas_used_pre_refund = intrinsic_cost_calc(
                authorization_list_or_count=authorization_list
            ) + code.gas_cost(fork)

            # Calculate refund (still applied to user's balance)
            gsc = fork.gas_costs()
            refund_counter = (
                gsc.REFUND_AUTH_PER_EXISTING_ACCOUNT * refunds_count
            )
            effective_refund = min(
                refund_counter, gas_used_pre_refund // max_refund_quotient
            )
            assert effective_refund > 0, (
                f"effective_refund ({effective_refund}) must be greater than 0"
            )
            gas_used_post_refund = gas_used_pre_refund - effective_refund

            refund_tx_gas_used = gas_used_pre_refund
            refund_tx_gas_spent = gas_used_post_refund

            refund_tx = Transaction(
                to=contract_address,
                gas_limit=refund_tx_gas_used,
                sender=refund_tx_sender,
                authorization_list=authorization_list,
                expected_receipt={
                    "gas_used": refund_tx_gas_used,
                    "gas_spent": refund_tx_gas_spent,
                },
            )
            refund_tx_gas_price = refund_tx.max_fee_per_gas

        case _:
            raise ValueError(
                f"Unknown refund type: {refund_type} (Test needs update)"
            )

    assert refund_tx_gas_price is not None, (
        "refund_tx_gas_price should not be None"
    )
    expected_balance = initial_fund - (
        refund_tx_gas_spent * refund_tx_gas_price
    )

    post[refund_tx_sender] = Account(balance=expected_balance)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[refund_tx],
                expected_gas_used=gas_used_pre_refund,
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
    max_refund_quotient = fork.max_refund_quotient()

    environment_gas_limit = 0
    refunds_count = 10
    initial_fund = 10**18

    refund_tx_sender = pre.fund_eoa(initial_fund)
    refund_tx_extra_gas = 1 if refund_tx_has_extra_gas_limit else 0

    stop_bytecode = Op.STOP
    stop_address = pre.deterministic_deploy_contract(deploy_code=stop_bytecode)

    post = {}

    match refund_type:
        case RefundTypes.STORAGE_CLEAR:
            # Refund happens due to a storage clearing
            storage_slots = list(range(refunds_count))

            code = Bytecode()
            for slot in storage_slots:
                code += Op.SSTORE(
                    slot,
                    Op.PUSH0,
                    # Gas accounting
                    original_value=1,
                    new_value=0,
                )
            if refund_tx_reverts:
                code += Op.REVERT(0, 0)

            contract_address = pre.deploy_contract(
                code=code,
                storage=dict.fromkeys(storage_slots, 1),
            )

            gas_used_pre_refund = intrinsic_cost_calc() + code.gas_cost(fork)

            # Calculate refund (still applied to user's balance)
            refund_counter = code.refund(fork)
            effective_refund = min(
                refund_counter, gas_used_pre_refund // max_refund_quotient
            )
            assert effective_refund > 0, (
                f"effective_refund ({effective_refund}) must be greater than 0"
            )
            gas_used_post_refund = gas_used_pre_refund - effective_refund

            refund_tx_gas_used = gas_used_pre_refund
            refund_tx_gas_spent = gas_used_post_refund

            if refund_tx_reverts:
                refund_tx_gas_spent = refund_tx_gas_used

            refund_tx = Transaction(
                to=contract_address,
                gas_limit=gas_used_pre_refund + refund_tx_extra_gas,
                sender=refund_tx_sender,
                expected_receipt={
                    "gas_used": refund_tx_gas_used,
                    "gas_spent": refund_tx_gas_spent,
                },
            )

            refund_tx_gas_price = refund_tx.gas_price

            if exceed_block_gas_limit or refund_tx_reverts:
                post[contract_address] = Account(
                    storage=dict.fromkeys(storage_slots, 1),
                )
            else:
                post[contract_address] = Account(
                    storage=dict.fromkeys(storage_slots, 0),
                )

        case RefundTypes.AUTHORIZATION_EXISTING_AUTHORITY:
            if refund_tx_reverts:
                code = Op.REVERT(0, 0)
                contract_address = pre.deterministic_deploy_contract(
                    deploy_code=code
                )
            else:
                code = stop_bytecode
                contract_address = stop_address
            authorization_list = [
                AuthorizationTuple(
                    address=contract_address,
                    nonce=0,
                    signer=pre.fund_eoa(amount=1),
                )
                for _ in range(refunds_count)
            ]
            gas_used_pre_refund = intrinsic_cost_calc(
                authorization_list_or_count=authorization_list
            ) + code.gas_cost(fork)

            # Calculate refund (still applied to user's balance)
            gsc = fork.gas_costs()
            refund_counter = (
                gsc.REFUND_AUTH_PER_EXISTING_ACCOUNT * refunds_count
            )
            effective_refund = min(
                refund_counter, gas_used_pre_refund // max_refund_quotient
            )
            assert effective_refund > 0, (
                f"effective_refund ({effective_refund}) must be greater than 0"
            )
            gas_used_post_refund = gas_used_pre_refund - effective_refund

            refund_tx_gas_used = gas_used_pre_refund
            refund_tx_gas_spent = gas_used_post_refund

            refund_tx = Transaction(
                to=contract_address,
                gas_limit=gas_used_pre_refund + refund_tx_extra_gas,
                sender=refund_tx_sender,
                authorization_list=authorization_list,
                expected_receipt={
                    "gas_used": refund_tx_gas_used,
                    "gas_spent": refund_tx_gas_spent,
                },
            )
            refund_tx_gas_price = refund_tx.max_fee_per_gas
        case _:
            raise ValueError(
                f"Unknown refund type: {refund_type} (Test needs update)"
            )

    assert refund_tx_gas_price is not None, (
        "refund_tx_gas_price should not be None"
    )
    expected_balance = initial_fund - (
        refund_tx_gas_spent * refund_tx_gas_price
    )

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

    total_gas_used = refund_tx_gas_used + extra_tx_intrinsic_gas_cost
    if exceed_block_gas_limit:
        environment_gas_limit = total_gas_used - 1
    else:
        environment_gas_limit = total_gas_used
        post[refund_tx_sender] = Account(balance=expected_balance)

    txs = [refund_tx, extra_tx]

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=BlockException.GAS_USED_OVERFLOW
                if exceed_block_gas_limit
                else None,
                expected_gas_used=total_gas_used
                if not exceed_block_gas_limit
                else None,
                gas_limit=environment_gas_limit,
            )
        ],
        post=post,
        genesis_environment=Environment(gas_limit=environment_gas_limit),
    )
