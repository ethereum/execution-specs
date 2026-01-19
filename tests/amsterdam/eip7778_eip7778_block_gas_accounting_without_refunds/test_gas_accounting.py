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
    Bytecode,
    Environment,
    Fork,
    Hash,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7928.md"
REFERENCE_SPEC_VERSION = "DUMMY_VERSION"


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
        expected_receipt={"gas_used": gas_used_pre_refund},
    )

    gas_price = tx.gas_price or 10
    # User still receives refund - they pay POST-refund amount
    expected_balance = initial_fund - gas_used_post_refund * gas_price

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


@pytest.mark.valid_from("Amsterdam")
def test_multi_block_gas_accounting(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    env: Environment,
) -> None:
    """Test the maximum gas refund behavior according to EIP-3529."""
    gas_costs = fork.gas_costs()
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()

    # Base Operation: SSTORE(slot, 0)
    iteration_cost = (
        gas_costs.G_COLD_SLOAD
        + gas_costs.G_STORAGE_RESET
        + gas_costs.G_BASE
        + gas_costs.G_VERY_LOW
    )

    txs = []
    post = {}
    total_gas_used = 0

    assert env.gas_limit is not None, "env.gas_limit must be set"
    assert tx_gas_limit_cap is not None, "tx_gas_limit_cap must be set"
    gas_remaining: int = env.gas_limit

    while gas_remaining > 0:
        tx_intrinsic = intrinsic_cost()
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
        tx_cost = tx_intrinsic + actual_execution_gas

        total_gas_used += tx_cost
        gas_remaining -= tx_cost

        tx = Transaction(
            to=contract,
            sender=pre.fund_eoa(),
            gas_limit=tx_cost,
            # Transaction receipt being the cumulative gas used
            expected_receipt={"gas_used": total_gas_used},
        )

        txs.append(tx)
        post[contract] = Account(
            storage={i: Hash(0) for i in range(iteration_count)}
        )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
        expected_gas_used=total_gas_used,
    )
