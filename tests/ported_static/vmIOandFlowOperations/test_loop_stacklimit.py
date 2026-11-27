"""
Test a loop that grows the stack up to, and past, the stack limit.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml

@manually-enhanced: Do not overwrite. The `looper` counts down from its
call value and leaves one extra item on the stack per iteration, so a loop
of `n` iterations peaks at `n + 4` items. The `caller` calls it with the
iteration count as value and stores the call's success flag and the
returned iteration counter. The filler's dispatcher passed the
transaction's value of 1, so its `loop_1020` and `loop_1021` cases looped
once and never reached the limit; here the counts come from the fork's
stack limit, so one loop peaks exactly at the limit and succeeds, and the
next overflows it and fails.
"""

from enum import StrEnum

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/VMTests/vmIOandFlowOperations/loop_stacklimitFiller.yml"
        ],
    ),
    pytest.mark.valid_from("Frontier"),
]

SUCCESS_SLOT = 0
COUNTER_SLOT = 1
SENTINEL = 0x0BAD
# How far the stack peaks above the iteration count.
PEAK_ABOVE_ITERATIONS = 4
# Explicit, so the call does not ask for more gas than is left before
# EIP-150 lets it forward all but 1/64th.
LOOPER_GAS = 0x100000


class LoopLength(StrEnum):
    """How many iterations the looper runs, relative to the stack limit."""

    ONE_ITERATION = "one_iteration"
    AT_STACK_LIMIT = "at_stack_limit"
    OVER_STACK_LIMIT = "over_stack_limit"


@pytest.fixture
def looper(pre: Alloc) -> Address:
    """
    Deploy the filler's loop, returning its iteration counter.

    The stack holds a leftover copy of each earlier countdown value below
    the counter and the countdown value. Each iteration decrements the
    countdown, increments the counter, and keeps a copy of the new
    countdown value, so the stack grows by one item per iteration.
    """
    setup = Op.PUSH1[0] + Op.CALLVALUE
    loop_start = len(setup)
    code = (
        setup
        + Op.JUMPDEST
        # countdown -= 1
        + Op.PUSH1[1]
        + Op.SWAP1
        + Op.SUB
        # counter += 1
        + Op.SWAP1
        + Op.PUSH1[1]
        + Op.ADD
        # Keep a copy of the countdown, and loop while it is non-zero.
        + Op.DUP2
        + Op.JUMPI(pc=loop_start, condition=Op.DUP1)
        + Op.PUSH1[0]
        + Op.MSTORE
        # The counter is stored at offset 1, as in the filler.
        + Op.PUSH1[1]
        + Op.MSTORE
        + Op.RETURN(1, 0x20)
    )
    return pre.deploy_contract(code=code)


@pytest.mark.parametrize("loop_length", list(LoopLength), ids=str)
def test_loop_stacklimit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    looper: Address,
    loop_length: LoopLength,
) -> None:
    """Run the loop and check whether it fits in the stack."""
    at_limit = fork.max_stack_height() - PEAK_ABOVE_ITERATIONS
    match loop_length:
        case LoopLength.ONE_ITERATION:
            iterations = 1
        case LoopLength.AT_STACK_LIMIT:
            iterations = at_limit
        case LoopLength.OVER_STACK_LIMIT:
            iterations = at_limit + 1
    overflows = loop_length == LoopLength.OVER_STACK_LIMIT

    caller = pre.deploy_contract(
        code=Op.SSTORE(
            SUCCESS_SLOT,
            Op.CALL(
                gas=LOOPER_GAS,
                address=looper,
                value=iterations,
                ret_offset=0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(COUNTER_SLOT, Op.MLOAD(0))
        + Op.STOP,
        storage={SUCCESS_SLOT: SENTINEL, COUNTER_SLOT: SENTINEL},
        balance=iterations,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        protected=fork.supports_protected_txs(),
    )

    # A failed call returns nothing, leaving the return buffer empty.
    storage = {SUCCESS_SLOT: 1, COUNTER_SLOT: iterations}
    if overflows:
        storage = {SUCCESS_SLOT: 0, COUNTER_SLOT: 0}
    post = {caller: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
