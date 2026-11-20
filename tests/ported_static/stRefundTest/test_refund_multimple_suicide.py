"""
Test the refund for a contract that calls itself to self-destruct twice.

Ported from:
state_tests/stRefundTest/refund_multimpleSuicideFiller.json

@manually-enhanced: Do not overwrite. The compiled contract is split into
its basic blocks so the gas of the executed path, including both inner
self-destruct calls, comes from `gas_cost(fork)`. The account is refunded
once, the cap comes from the fork, the post branches on EIP-6780, and the
fee recipient's priority fee is checked with `Tip`.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BlockReward,
    Bytes,
    Environment,
    Fork,
    GasFee,
    StateTestFiller,
    Tip,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACT_BALANCE = 0xDE0B6B3A7640000
ADDRESS_MASK = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
DESTROY_SELECTOR = 0x9E587A5
RUN_SELECTOR = 0xC0406226
# Solidity's free-memory pointer: the slot at 0x40 holds 0x60, so the
# dispatcher grows memory to three words and the call data written at
# 0x60 grows it to four.
FREE_MEMORY_POINTER = 0x40
FREE_MEMORY_START = 0x60
CALL_DATA_END = FREE_MEMORY_START + 32


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_multimpleSuicideFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.execute(
    pytest.mark.skip(reason="requires env.fee_recipient as block coinbase")
)
def test_refund_multimple_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Call the contract's own `destroy()` twice; refund it only once."""
    sender = pre.fund_eoa()

    # The contract is the Solidity output of the original filler. Each
    # piece below is one basic block, so the gas of the blocks that run
    # can be read off the bytecode.
    dispatch_destroy = (
        Op.MSTORE(
            offset=FREE_MEMORY_POINTER,
            value=FREE_MEMORY_START,
            new_memory_size=FREE_MEMORY_START,
        )
        + Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xE0, exponent=0xE0))
        + Op.JUMPI(
            pc=Op.PUSH2[0x31], condition=Op.EQ(Op.DUP2, DESTROY_SELECTOR)
        )
    )
    dispatch_run = Op.JUMPI(
        pc=Op.PUSH2[0x4D], condition=Op.EQ(RUN_SELECTOR, Op.DUP1)
    )
    dispatch_other = Op.JUMPI(
        pc=Op.PUSH2[0x5A], condition=Op.EQ(0xDD4F1F2A, Op.DUP1)
    )
    fallback = Op.JUMPDEST + Op.STOP
    # destroy(): self-destruct to the caller, which is the contract
    # itself. From EIP-6780 on a pre-existing contract is not deleted.
    destroy = (
        Op.JUMPDEST
        + Op.PUSH2[0x2F]
        + Op.SELFDESTRUCT(
            address=Op.AND(ADDRESS_MASK, Op.CALLER),
            address_warm=True,
            account_new=False,
            self_destructed_account=not fork.is_eip_enabled(6780),
        )
    )
    run_entry = (
        Op.JUMPDEST
        + Op.PUSH2[0xF5]
        + Op.PUSH1[0x0]
        + Op.PUSH2[0x109]
        + Op.JUMP(pc=Op.PUSH2[0x5E])
    )
    other_entry = Op.JUMPDEST + Op.PUSH2[0x2F]
    # Each inner call runs the dispatcher and destroy() in a fresh frame.
    inner_call_cost = (dispatch_destroy + destroy).gas_cost(fork)
    first_call_destroy = (
        Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.ADDRESS
        + Op.SWAP1
        + Op.POP
        + Op.AND(ADDRESS_MASK, Op.DUP1)
        + Op.PUSH4[DESTROY_SELECTOR]
        + Op.MLOAD(offset=FREE_MEMORY_POINTER)
        + Op.MSTORE(
            offset=Op.DUP2,
            value=Op.MUL(Op.EXP(0x2, 0xE0, exponent=0xE0), Op.DUP2),
            old_memory_size=FREE_MEMORY_START,
            new_memory_size=CALL_DATA_END,
        )
        + Op.PUSH1[0x4]
        + Op.ADD
        + Op.DUP1
        + Op.SWAP1
        + Op.POP
        + Op.JUMPI(
            pc=Op.PUSH2[0x2],
            condition=Op.ISZERO(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x61DA),
                    address=Op.DUP8,
                    value=0x0,
                    args_offset=Op.DUP2,
                    args_size=Op.SUB(Op.DUP4, Op.DUP1),
                    ret_offset=Op.MLOAD(offset=FREE_MEMORY_POINTER),
                    ret_size=0x0,
                    address_warm=True,
                    inner_call_cost=inner_call_cost,
                )
            ),
        )
    )
    second_call_destroy = (
        Op.POP
        + Op.PUSH1[FREE_MEMORY_POINTER]
        + Op.MLOAD(offset=Op.DUP1)
        + Op.MSTORE(
            offset=Op.DUP2,
            value=DESTROY_SELECTOR << 224,
        )
        + Op.SWAP1
        + Op.MLOAD
        + Op.PUSH1[0x4]
        + Op.ADD(Op.DUP2, Op.DUP3)
        + Op.SWAP3
        + Op.PUSH1[0x0]
        + Op.SWAP3
        + Op.SWAP2
        + Op.SWAP1
        + Op.DUP3
        + Op.SWAP1
        + Op.SUB
        + Op.ADD
        + Op.DUP2
        + Op.DUP4
        + Op.DUP8
        + Op.SUB(Op.GAS, 0x61DA)
        + Op.JUMPI(
            pc=Op.PUSH2[0x2],
            condition=Op.ISZERO(
                Op.CALL.with_metadata(
                    address_warm=True, inner_call_cost=inner_call_cost
                )
            ),
        )
    )
    cleanup = Op.POP * 4 + Op.JUMP
    return_bool = (
        Op.JUMPDEST
        + Op.PUSH1[FREE_MEMORY_POINTER]
        + Op.MLOAD(offset=Op.DUP1)
        + Op.SWAP2
        + Op.MSTORE(offset=Op.DUP3, value=Op.ISZERO(Op.ISZERO))
        + Op.MLOAD
        + Op.SWAP1
        + Op.DUP2
        + Op.SWAP1
        + Op.ADD(0x20, Op.SUB)
        + Op.SWAP1
        + Op.RETURN
    )
    set_true = Op.JUMPDEST + Op.POP + Op.PUSH1[0x1] + Op.SWAP1 + Op.JUMP
    target = pre.deploy_contract(
        code=dispatch_destroy
        + dispatch_run
        + dispatch_other
        + fallback
        + destroy
        + run_entry
        + other_entry
        + first_call_destroy
        + second_call_destroy
        + cleanup
        + return_bool
        + set_true,
        balance=CONTRACT_BALANCE,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(RUN_SELECTOR.to_bytes(4, "big")),
        gas_limit=300000,
        protected=fork.supports_protected_txs(),
    )

    # run() dispatches, calls destroy() twice and returns true.
    executed_path = (
        dispatch_destroy
        + dispatch_run
        + run_entry
        + first_call_destroy
        + second_call_destroy
        + cleanup
        + set_true
        + return_bool
    )
    gas_before_refund = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx.data, return_cost_deducted_prior_execution=True
    ) + executed_path.gas_cost(fork)
    # An account that self-destructs twice is refunded once.
    refund = min(
        destroy.refund(fork), gas_before_refund // fork.max_refund_quotient()
    )
    gas_used = gas_before_refund - refund

    post = {
        # Self-destructing to itself burns the balance of a deleted
        # contract; from EIP-6780 on the contract and balance remain.
        target: (
            Account(balance=CONTRACT_BALANCE)
            if fork.is_eip_enabled(6780)
            else Account.NONEXISTENT
        ),
        sender: Account(balance_change=-GasFee(tx, gas=gas_used)),
    }
    # Before the Merge the coinbase also receives the block reward.
    post[Environment().fee_recipient] = Account(
        balance_change=Tip(tx, gas=gas_used) + BlockReward(tx)
    )

    state_test(pre=pre, post=post, tx=tx)
