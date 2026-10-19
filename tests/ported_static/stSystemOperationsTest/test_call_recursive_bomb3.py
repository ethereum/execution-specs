"""
Verify a self-recursive CALL bomb that keeps only a 224-gas reserve.

Each level bumps a shared depth counter and forwards everything but a
tiny reserve to a call to itself, so descent is throttled only by the
EIP-150 63/64 withhold. On the way back up a level must afford its
success-flag store from its 1/64 retention plus whatever its child
returned; levels that cannot (EIP-2200's stipend rule included) halt
and forfeit, so the surviving storage pins the exact depth the budget
sustains.

Ported from:
state_tests/stSystemOperationsTest/CallRecursiveBomb3Filler.json

@manually-enhanced: Do not overwrite. The post state is predicted by an
exact fork-derived replay of the recursion's gas flow (EIP-150 grants,
returned-leftover propagation, warm/cold and SSTORE pricing via opcode
metadata, EIP-8037 state-gas spill), validated against the ported
Cancun depth. Under Amsterdam's revised storage-growth pricing even the
top level cannot afford its zero-to-one flag store at the ported
budget, so the whole transaction reverts and the post pins empty
storage.
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

COUNTER_SLOT = 0
RESULT_SLOT = 1
# Gas each level keeps back; far below a cold store, so completing the
# post-call flag store depends on the 1/64 retention and the child's
# returned leftover.
GAS_RESERVE = 224
# Ported budget; pins the OOG-terminated depth.
TX_GAS_LIMIT = 1_000_000

RECURSION_CODE = (
    Op.SSTORE(
        key=COUNTER_SLOT,
        value=Op.ADD(Op.SLOAD(key=COUNTER_SLOT), 1),
    )
    + Op.SSTORE(
        key=RESULT_SLOT,
        value=Op.CALL(
            gas=Op.SUB(Op.GAS, GAS_RESERVE),
            address=Op.ADDRESS,
        ),
    )
    + Op.STOP
)


def predict_recursion_storage(fork: Fork, tx_gas_limit: int) -> dict[int, int]:
    """
    Replay the recursion's gas flow and return the surviving storage.

    Descend the self-call chain computing each level's EIP-150 grant,
    then unwind: a level that cannot afford its flag store halts and
    forfeits its entire grant to its parent, so the deepest level that
    completes fixes the surviving depth counter (deeper levels' writes
    and warmth all revert). The level above the deepest survivor funds
    its more expensive zero-to-one flag set partly from the survivor's
    returned leftover. Every cost is derived from the fork via opcode
    metadata, including EIP-8037 state gas: with a sub-cap gas limit
    the state reservoir is zero, so state charges spill from the
    charging frame's own gas.
    """
    push_cost = Op.PUSH1[0].gas_cost(fork)
    # The ask expression's SUB runs after GAS reads gas_left.
    post_gas_read = Op.SUB.gas_cost(fork)
    # EIP-2200: any SSTORE with gas_left <= stipend halts exceptionally.
    stipend = fork.gas_costs().CALL_STIPEND

    def raw_store_cost(key_warm: bool, current: int, new: int) -> int:
        """Cost of a bare SSTORE; original value is always zero here."""
        return Op.SSTORE(
            key_warm=key_warm,
            original_value=0,
            current_value=current,
            new_value=new,
        ).gas_cost(fork)

    sstore_warm_set = raw_store_cost(True, 0, 1)
    sstore_warm_dirty = raw_store_cost(True, 1, 2)
    sstore_warm_noop = raw_store_cost(True, 1, 1)
    sstore_cold_noop = raw_store_cost(False, 0, 0)

    def bump_statics(key_warm: bool) -> int:
        """Counter-bump costs before its SSTORE (value expr plus key)."""
        return (
            Op.ADD(Op.SLOAD(key=COUNTER_SLOT, key_warm=key_warm), 1).gas_cost(
                fork
            )
            + push_cost
        )

    bump_statics_cold = bump_statics(False)
    bump_statics_warm = bump_statics(True)

    ask_expr = Op.SUB(Op.GAS, GAS_RESERVE)
    call_upfront = Op.CALL(address_warm=True).gas_cost(fork)
    # Everything charged before GAS reads gas_left: the call's argument
    # pushes, ADDRESS, and the reserve push plus the GAS opcode itself.
    pre_gas_read = (
        Op.CALL(gas=ask_expr, address=Op.ADDRESS, address_warm=True).gas_cost(
            fork
        )
        - call_upfront
        - post_gas_read
    )

    # Descend: compute each level's grant until a level dies mid-frame.
    gas = (
        tx_gas_limit
        - fork.transaction_intrinsic_cost_calculator()()
        - fork.transaction_top_frame_state_gas()
    )
    levels: list[tuple[int, int]] = []
    level = 0
    while True:
        level += 1
        first = level == 1
        gas -= bump_statics_cold if first else bump_statics_warm
        if gas < 0 or gas <= stipend:
            break
        gas -= sstore_warm_set if first else sstore_warm_dirty
        if gas < 0:
            break
        gas -= pre_gas_read
        if gas < 0:
            break
        gas_read = gas
        gas -= post_gas_read + call_upfront
        if gas < 0:
            break
        assert level < 1024, "recursion must die of gas, not depth"
        # A reserve underflow wraps mod 2**256: an effectively infinite
        # ask, clamped to the 63/64 forwardable maximum.
        ask = gas_read - GAS_RESERVE if gas_read >= GAS_RESERVE else 1 << 256
        forwarded = min(ask, gas - gas // 64)
        levels.append((gas, forwarded))
        gas = forwarded

    # Unwind: a failed level forfeits its whole grant to its parent.
    child_ok = False
    result_below = 0
    leftover = 0
    survivor = 0
    for lvl in range(len(levels), 0, -1):
        available, forwarded = levels[lvl - 1]
        gas = available - forwarded + (leftover if child_ok else 0)
        # Flag store: push the slot key, then store the success flag.
        # Below the deepest completing level everything reverts, so its
        # own store finds a cold slot and a zero current value.
        gas -= push_cost
        ok = gas >= 0 and gas > stipend
        if ok:
            if not child_ok:
                result_store = sstore_cold_noop
            elif result_below == 0:
                result_store = sstore_warm_set
            else:
                result_store = sstore_warm_noop
            gas -= result_store
            ok = gas >= 0
        if ok:
            if not child_ok:
                survivor = lvl
            result_below = 1 if child_ok else 0
            leftover = gas
            child_ok = True
        else:
            child_ok = False
            result_below = 0
            leftover = 0
            survivor = 0
    if not child_ok:
        # The top level itself cannot afford its flag store (its
        # retention plus the child's leftover falls short of the
        # storage-growth cost), so the transaction halts and every
        # write reverts.
        return {COUNTER_SLOT: 0, RESULT_SLOT: 0}
    assert survivor > 0, "a completing top level must record a depth"
    return {COUNTER_SLOT: survivor, RESULT_SLOT: result_below}


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/CallRecursiveBomb3Filler.json"],
)
@pytest.mark.valid_from("Berlin")
def test_call_recursive_bomb3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Pin the depth a thin-reserve CALL self-recursion sustains."""
    target = pre.deploy_contract(code=RECURSION_CODE)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=target,
        gas_limit=TX_GAS_LIMIT,
    )

    post = {
        target: Account(storage=predict_recursion_storage(fork, TX_GAS_LIMIT)),
    }

    state_test(pre=pre, post=post, tx=tx)
