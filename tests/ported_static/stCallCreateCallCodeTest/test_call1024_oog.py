"""
Verify self-recursive CALL, CALLCODE and DELEGATECALL chains that
terminate by out-of-gas.

Each level bumps a shared depth counter, forwards almost all its gas to
a self-call (keeping a 10,000 reserve for its post-call stores), then
records the call's success flag and a depth marker. Levels too deep to
afford their stores halt and roll back, so the surviving storage pins
the exact depth the budget reaches under the EIP-150 63/64 rule.

Ported from:
state_tests/stCallCreateCallCodeTest/Call1024OOGFiller.json
state_tests/stCallCreateCallCodeTest/Callcode1024OOGFiller.json
state_tests/stDelegatecallTestHomestead/Call1024OOGFiller.json
state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json

@manually-enhanced: Do not overwrite. The post state is predicted by an
exact fork-derived replay of the recursion's gas flow (EIP-150 grants,
warm/cold and SSTORE pricing via opcode metadata, EIP-8037 state-gas
spill), validated against the ported Cancun depths; the hardcoded
self-address is replaced by ADDRESS. Four fillers from two legacy
suites are joined into one opcode parametrization, every budget run
against every opcode, so the whole scope is visible in one file.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

COUNTER_SLOT = 0
RESULT_SLOT = 1
MARKER_SLOT = 2
# Gas each level keeps back for its post-call stores.
GAS_RESERVE = 10_000
# The ask factor zeroes out at the call-depth limit (never reached here;
# the recursion always dies of out-of-gas first).
DEPTH_CUTOFF = 1025
# The marker store writes 1 + DEPTH_MARKER * depth.
DEPTH_MARKER = 1000


def recursion_code(call_opcode: Opcode) -> Bytecode:
    """Build the self-recursive body for the given call opcode."""
    return (
        Op.SSTORE(
            key=COUNTER_SLOT,
            value=Op.ADD(Op.SLOAD(key=COUNTER_SLOT), 1),
        )
        + Op.SSTORE(
            key=RESULT_SLOT,
            value=call_opcode(
                gas=Op.MUL(
                    Op.SUB(Op.GAS, GAS_RESERVE),
                    Op.SUB(
                        1, Op.DIV(Op.SLOAD(key=COUNTER_SLOT), DEPTH_CUTOFF)
                    ),
                ),
                address=Op.ADDRESS,
            ),
        )
        + Op.SSTORE(
            key=MARKER_SLOT,
            value=Op.ADD(1, Op.MUL(Op.SLOAD(key=COUNTER_SLOT), DEPTH_MARKER)),
        )
        + Op.STOP
    )


def predict_recursion_storage(
    fork: Fork, call_opcode: Opcode, tx_gas_limit: int
) -> dict[int, int]:
    """
    Replay the recursion's gas flow and return the surviving storage.

    Descend the self-call chain computing each level's EIP-150 grant,
    then unwind: a level that cannot afford its post-call stores halts
    and forfeits its entire grant to its parent, so the deepest level
    that completes fixes the surviving depth counter (deeper levels'
    writes and warmth all revert). Every cost is derived from the fork
    via opcode metadata, including EIP-8037 state gas: with a sub-cap
    gas limit the state reservoir is zero, so state charges spill from
    the charging frame's own gas.
    """
    push_cost = Op.PUSH1[0].gas_cost(fork)
    # The SUB and MUL of the ask expression run after GAS reads gas_left.
    post_gas_read = Op.SUB.gas_cost(fork) + Op.MUL.gas_cost(fork)
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
    sstore_cold_set = raw_store_cost(False, 0, 1)

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

    ask_expr = Op.MUL(
        Op.SUB(Op.GAS, GAS_RESERVE),
        Op.SUB(
            1,
            Op.DIV(Op.SLOAD(key=COUNTER_SLOT, key_warm=True), DEPTH_CUTOFF),
        ),
    )
    call_upfront = call_opcode(address_warm=True).gas_cost(fork)
    # Everything charged before GAS reads gas_left: the call's argument
    # pushes, ADDRESS, and the ask expression through the GAS opcode.
    pre_gas_read = (
        call_opcode(
            gas=ask_expr, address=Op.ADDRESS, address_warm=True
        ).gas_cost(fork)
        - call_upfront
        - post_gas_read
    )

    marker_statics = (
        Op.ADD(
            1,
            Op.MUL(Op.SLOAD(key=COUNTER_SLOT, key_warm=True), DEPTH_MARKER),
        ).gas_cost(fork)
        + push_cost
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
        assert level < DEPTH_CUTOFF, "recursion must die of gas, not depth"
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
        # Result store: push the slot key, then store the success flag.
        # Below the deepest completing level everything reverts, so its
        # own stores find cold slots and zero current values.
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
        # Marker store: parents rewrite the same surviving marker value.
        if ok:
            gas -= marker_statics
            ok = gas >= 0 and gas > stipend
        if ok:
            gas -= sstore_warm_noop if child_ok else sstore_cold_set
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
    assert child_ok and survivor > 0, "the top level must complete"
    return {
        COUNTER_SLOT: survivor,
        RESULT_SLOT: result_below,
        MARKER_SLOT: 1 + DEPTH_MARKER * survivor,
    }


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/Call1024OOGFiller.json",
        "state_tests/stCallCreateCallCodeTest/Callcode1024OOGFiller.json",
        "state_tests/stDelegatecallTestHomestead/Call1024OOGFiller.json",
        "state_tests/stDelegatecallTestHomestead/Delegatecall1024OOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
    ],
)
@pytest.mark.parametrize(
    # Ported budgets; each pins a distinct OOG-terminated depth.
    "tx_gas_limit",
    [13_120_826, 9_320_826, 15_720_826, 11_220_826],
)
def test_call1024_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcode,
    tx_gas_limit: int,
) -> None:
    """Pin the depth an OOG-terminated self-recursion reaches."""
    target = pre.deploy_contract(code=recursion_code(call_opcode))

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=target,
        gas_limit=tx_gas_limit,
    )

    post = {
        target: Account(
            storage=predict_recursion_storage(fork, call_opcode, tx_gas_limit)
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
