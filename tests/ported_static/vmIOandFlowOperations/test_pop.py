"""
Test POP.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/popFiller.yml

@manually-enhanced: Do not overwrite. Built from readable parameters.

Each contract pushes `stack_depth` distinct items with `PC`, so the
item `n` places from the bottom holds its offset `n - 1`, and then runs
its POPs.
`test_pop` pops some of the items and stores the top items that remain,
so the stored values show that exactly the popped items left the stack,
from the top. `test_pop_underflow` pops one item more than it pushed,
after a storage write, and expects the stack underflow to revert the
frame, write included, at every depth up to the stack limit.
"""

import pytest
from execution_testing import (
    Account,
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
        ["state_tests/VMTests/vmIOandFlowOperations/popFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
]

SENTINEL = 0x0BAD
DONE = 0x600D
WRITTEN = 0x1234

MAX_STACK_DEPTH = 1024
# How many of the remaining top items `test_pop` stores, the top one in
# slot 0, so a full stack doesn't cost a store per item.
STORED_ITEMS = 3
DONE_SLOT = STORED_ITEMS
# `test_pop_underflow` writes before the underflow and after it.
WRITTEN_SLOT = 0
SKIPPED_SLOT = 1


@pytest.mark.parametrize(
    "stack_depth, pops",
    [
        pytest.param(1, 1, id="pop_1_of_1"),
        pytest.param(3, 1, id="pop_1_of_3"),
        pytest.param(3, 2, id="pop_2_of_3"),
        pytest.param(MAX_STACK_DEPTH, 1, id="pop_1_of_max"),
        pytest.param(
            MAX_STACK_DEPTH, MAX_STACK_DEPTH - 1, id="pop_all_but_1_of_max"
        ),
    ],
)
def test_pop(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    stack_depth: int,
    pops: int,
) -> None:
    """Pop items and verify the top items that remain."""
    remaining = stack_depth - pops
    stored = min(remaining, STORED_ITEMS)
    # Each PC pushes its own offset, so every item is distinct.
    code = Op.PC * stack_depth + Op.POP * pops
    for slot in range(stored):
        # Store the current top item, consuming it.
        code += Op.PUSH1[slot] + Op.SSTORE
    code += Op.SSTORE(DONE_SLOT, DONE) + Op.STOP

    contract = pre.deploy_contract(
        code=code,
        storage=dict.fromkeys(range(DONE_SLOT + 1), SENTINEL),
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )

    storage = dict.fromkeys(range(STORED_ITEMS), SENTINEL)
    for slot in range(stored):
        storage[slot] = remaining - 1 - slot
    storage[DONE_SLOT] = DONE
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "stack_depth",
    [0, 1, 2, MAX_STACK_DEPTH],
    ids=lambda stack_depth: f"stack_depth_{stack_depth}",
)
def test_pop_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    stack_depth: int,
) -> None:
    """Revert the frame when POP runs on a stack it has emptied."""
    code = (
        Op.SSTORE(WRITTEN_SLOT, WRITTEN)
        + Op.PC * stack_depth
        + Op.POP * (stack_depth + 1)
        + Op.SSTORE(SKIPPED_SLOT, DONE)
        + Op.STOP
    )

    contract = pre.deploy_contract(
        code=code, storage={WRITTEN_SLOT: SENTINEL, SKIPPED_SLOT: SENTINEL}
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )

    # The underflow reverts the write before it and skips the one after.
    storage = {WRITTEN_SLOT: SENTINEL, SKIPPED_SLOT: SENTINEL}
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
