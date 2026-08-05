"""
Verify a two-level call chain (with memory-expanding call windows) where
the second-level frame runs out of gas: its own frame and everything below
it revert, while the top frame survives and records the failure.

Ported from:
state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json

@manually-enhanced: Do not overwrite. The first-level budget is pinned and
derived from the fork so the second level keeps starving on every fork
(its 1/64 retention cannot afford the post-call store); the second-level
ask stays oversized; the top frame's entry snapshot is derived and pins
the transaction intrinsic.
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

SNAPSHOT_SLOT = 0x8
FLAG_SLOT = 0x9
# The ported second-level ask: far above the pinned budget.
ASK_GAS = 0x927C0
# The ported calls' argument window, driving the memory expansion.
MEM_OFFSET = 0xFF
MEM_SIZE = 0xFF


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
def test_call_goes_oog_on_second_level_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A starved second-level frame reverts itself and everything below."""
    # Deepest contract: snapshots and creates twice; its cost anchors the
    # starvation budget.
    deep_snapshot = Op.SSTORE(
        key=SNAPSHOT_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    deep = pre.deploy_contract(
        code=deep_snapshot
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0)) * 2
        + Op.SSTORE(key=FLAG_SLOT, value=Op.GAS)
        + Op.SSTORE(key=0xA, value=Op.GAS),
    )

    # Second level: snapshots, then asks far more than it holds; the ported
    # memory-expanding argument window is kept.
    mid = pre.deploy_contract(
        code=Op.SSTORE(key=SNAPSHOT_SLOT, value=Op.GAS)
        + Op.SSTORE(
            key=FLAG_SLOT,
            value=Op.CALL(
                gas=ASK_GAS,
                address=deep,
                args_offset=MEM_OFFSET,
                args_size=MEM_SIZE,
                ret_offset=MEM_OFFSET,
                ret_size=MEM_SIZE,
            ),
        ),
    )

    # Pin the second level's budget so it starves on every fork: enough
    # to pay its own snapshot and call, but its grant to the deep frame
    # undercuts the deep frame's first store, and its 1/64 retention
    # cannot afford its own post-call flag store.
    mid_snapshot_cost = Op.SSTORE(
        key=SNAPSHOT_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    ).gas_cost(fork)
    mid_call_cost = Op.CALL(
        gas=ASK_GAS,
        address=deep,
        args_offset=MEM_OFFSET,
        args_size=MEM_SIZE,
        ret_offset=MEM_OFFSET,
        ret_size=MEM_SIZE,
        address_warm=False,
        account_new=False,
        new_memory_size=MEM_OFFSET + MEM_SIZE,
    ).gas_cost(fork)
    deep_needed = deep_snapshot.gas_cost(fork)
    caller_gas = mid_snapshot_cost + mid_call_cost + deep_needed // 2
    assert caller_gas < ASK_GAS, "the second-level ask must exceed its frame"

    # Top frame: derived entry snapshot (pins the intrinsic), the pinned
    # call, and the failure flag.
    entry_snapshot = Op.SSTORE(
        key=SNAPSHOT_SLOT,
        value=Op.GAS,
        key_warm=False,
        original_value=0,
        new_value=1,
    )
    flag_store = Op.SSTORE(
        key=FLAG_SLOT,
        value=Op.CALL(
            gas=caller_gas,
            address=mid,
            args_offset=MEM_OFFSET,
            args_size=MEM_SIZE,
            ret_offset=MEM_OFFSET,
            ret_size=MEM_SIZE,
            address_warm=False,
            account_new=False,
            new_memory_size=MEM_OFFSET + MEM_SIZE,
        ),
        key_warm=False,
        original_value=0,
        new_value=0,
    )
    target = pre.deploy_contract(
        code=entry_snapshot + flag_store + Op.STOP,
    )

    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = (
        intrinsic
        + entry_snapshot.gas_cost(fork)
        + flag_store.gas_cost(fork)
        + caller_gas
        + 5_000
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=target,
        gas_limit=gas_limit,
    )

    post = {
        # The failed call's flag slot stays zero; the entry snapshot pins
        # the intrinsic.
        target: Account(
            storage={
                SNAPSHOT_SLOT: gas_limit - intrinsic - Op.GAS.gas_cost(fork),
            },
        ),
        # Both lower frames reverted entirely.
        mid: Account(storage={}),
        deep: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
