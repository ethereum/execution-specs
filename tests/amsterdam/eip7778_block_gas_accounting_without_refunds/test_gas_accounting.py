"""
Test cases for
[EIP-7778 Block Gas Accounting without Refunds](https://eips.ethereum.org/EIPS/eip-7778).
"""

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
    Hash,
    Transaction,
    TransactionException,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7778.md"
REFERENCE_SPEC_VERSION = "54fba02495a05b57acd3f27473d0493b40a9d920"


@pytest.mark.valid_from("Amsterdam")
def test_simple_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test gas accounting when SSTORE refunds."""
    gsc = fork.gas_costs()
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_refund_quotient = fork.max_refund_quotient()

    num_slot = 10

    # gas cost for SSTORE(slot, 0), resetting storage to zero
    per_slot_cost = (
        gsc.G_BASE + gsc.G_VERY_LOW + gsc.G_COLD_SLOAD + gsc.G_STORAGE_RESET
    )
    gas_used_pre_refund = intrinsic_cost_calc() + per_slot_cost * num_slot

    # Calculate refund (still applied to user's balance)
    refund_counter = gsc.R_STORAGE_CLEAR * num_slot
    effective_refund = min(
        refund_counter, gas_used_pre_refund // max_refund_quotient
    )
    gas_used_post_refund = gas_used_pre_refund - effective_refund

    initial_fund = 10**18
    sender = pre.fund_eoa(initial_fund)

    storage_slots = list(range(num_slot))

    code = Bytecode()
    for slot in storage_slots:
        code += Op.SSTORE(slot, Op.PUSH0)

    contract_address = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(storage_slots, 1),
    )

    tx = Transaction(
        to=contract_address,
        gas_limit=fork.transaction_gas_limit_cap(),
        sender=sender,
        expected_receipt={
            "gas_used": gas_used_pre_refund,
            "gas_spent": gas_used_post_refund,
        },
    )

    assert tx.gas_price is not None, "tx.gas_price should not be None"
    expected_balance = initial_fund - gas_used_post_refund * tx.gas_price

    post = {
        contract_address: Account(
            storage=dict.fromkeys(storage_slots, 0),
        ),
        sender: Account(balance=expected_balance),
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
        expected_gas_used=gas_used_pre_refund,
    )


@pytest.mark.parametrize(
    "exceed_block_gas_limit",
    [
        pytest.param(True, marks=pytest.mark.exception_test),
        False,
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_multi_block_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    env: Environment,
    exceed_block_gas_limit: bool,
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
    gas_costs = fork.gas_costs()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
    max_refund_quotient = fork.max_refund_quotient()

    # Base Operation: SSTORE(slot, 0) - clearing storage
    iteration_cost = (
        gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
        + gas_costs.G_BASE
        + gas_costs.G_VERY_LOW
    )
    refund_per_slot = gas_costs.R_STORAGE_CLEAR

    txs = []
    post = {}
    total_gas_used = 0  # Pre-refund (for block gas accounting per EIP-7778)
    total_gas_spent = 0  # Post-refund (what users actually pay)

    assert env.gas_limit is not None, "env.gas_limit must be set"
    assert tx_gas_limit_cap is not None, "tx_gas_limit_cap must be set"

    block_gas_limit: int = env.gas_limit
    tx_intrinsic = intrinsic_cost_calc()

    # Target gas to use (pre-refund)
    # For exceed_block_gas_limit:
    # - pre-refund > (block_gas_limit - tx_intrinsic)
    # - post-refund <= (block_gas_limit - tx_intrinsic)
    target_gas_pre_refund = block_gas_limit

    gas_remaining = target_gas_pre_refund

    while gas_remaining > 0:
        if gas_remaining < tx_intrinsic:
            break

        max_tx_gas = min(gas_remaining, tx_gas_limit_cap)
        execution_gas = max_tx_gas - tx_intrinsic

        iteration_count = min(
            execution_gas // iteration_cost,
            fork.max_code_size() // len(Op.SSTORE(0xFFFF, Op.PUSH0)),
        )

        if iteration_count == 0:
            break

        opcode = sum(
            (Op.SSTORE(i, Op.PUSH0) for i in range(iteration_count)),
            Bytecode(),
        )

        contract = pre.deploy_contract(
            code=opcode,
            storage={i: Hash(1) for i in range(iteration_count)},
        )

        actual_execution_gas = iteration_cost * iteration_count
        tx_gas_pre_refund = tx_intrinsic + actual_execution_gas

        # Calculate effective refund (capped at gas_used / max_refund_quotient)
        refund_counter = refund_per_slot * iteration_count
        effective_refund = min(
            refund_counter, tx_gas_pre_refund // max_refund_quotient
        )
        tx_gas_post_refund = tx_gas_pre_refund - effective_refund

        total_gas_used += tx_gas_pre_refund
        total_gas_spent += tx_gas_post_refund
        gas_remaining -= tx_gas_pre_refund

        tx = Transaction(
            to=contract,
            sender=pre.fund_eoa(),
            gas_limit=tx_gas_pre_refund,
            expected_receipt={
                "gas_used": total_gas_used,
                "gas_spent": tx_gas_post_refund,
            },
        )

        txs.append(tx)
        post[contract] = Account(
            storage={i: Hash(0) for i in range(iteration_count)}
        )

    if exceed_block_gas_limit:
        threshold = block_gas_limit - tx_intrinsic
        assert total_gas_used > threshold, (
            f"Pre-refund gas {total_gas_used} <= threshold {threshold}"
        )
        assert total_gas_spent <= threshold, (
            f"Post-refund gas {total_gas_spent} > threshold {threshold}"
        )

        tx = Transaction(
            to=pre.fund_eoa(),
            sender=pre.fund_eoa(),
            gas_limit=tx_intrinsic,
            value=1,
            error=TransactionException.GAS_ALLOWANCE_EXCEEDED,
        )
        txs.append(tx)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=txs,
                exception=BlockException.GAS_USED_OVERFLOW
                if exceed_block_gas_limit
                else None,
            )
        ],
        post=post if not exceed_block_gas_limit else {},
        expected_gas_used=total_gas_used
        if not exceed_block_gas_limit
        else None,
    )
