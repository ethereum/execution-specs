"""
Verify EIP-150's "all but one 64th" retention across a three-level call
chain: a frame whose callee consumes its entire grant is left with only
`floor(N / 64)`, and whether that retention covers the frame's remaining
work is what decides how far up the chain the failure propagates.

Ported from:
state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json
state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json
state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json

@manually-enhanced: Do not overwrite. The three fillers ran one program at
three budgets, landing either side of a boundary none of them located.
Here the only tuned value is the gas operand of the entry's call, set one
gas either side of the derived boundary, so the transaction budget carries
no meaning. The second level reports upward with RETURN rather than
SSTORE -- the static filler had to swap to MSTORE for exactly this
reason -- so one program serves every call opcode. The `*OnSecondLevel2*`
filler of all three directories was dropped: each asserted empty storage
on all three accounts, which only says the transaction ran out before
doing anything.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Opcodes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

FLAG_SLOT = 0x9
# Seeded into the entry's flag slot, so "the entry never ran" stays
# distinct from "it ran and its callee never reported back".
SENTINEL = 0x60A7

# The ported argument/return window, used by the `mem_expansion` cases.
# It is not decoration: its expansion is part of each CALL's own cost, and
# so part of the boundary below -- mispricing it by a gas flips a case.
MEM_WINDOW = 0xFF

# The ported memory bomb: the third level can never afford it, so it burns
# its whole grant and returns nothing. That is what leaves its caller on
# the bare 1/64 retention.
MEM_BOMB = 0x2FFFFF


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json",
        "state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json",
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.parametrize(
    "memory_expansion", [False, True], ids=["flat", "mem_expansion"]
)
@pytest.mark.parametrize("second_level", ["survives", "starved"])
@pytest.mark.with_all_call_opcodes
def test_call_goes_oog_on_second_level(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Opcodes,
    second_level: str,
    memory_expansion: bool,
) -> None:
    """One gas of retention decides whether the second level survives."""
    # Third level: burns its entire grant on a memory bomb it can never
    # afford, so it returns nothing to its caller.
    third_level = pre.deploy_contract(
        code=Op.POP(Op.SHA3(offset=0x0, size=MEM_BOMB)) + Op.STOP
    )

    # At zero the window costs nothing; at MEM_WINDOW its expansion is
    # what the `*WithMemExpandingCalls` fillers exist to exercise.
    window = MEM_WINDOW if memory_expansion else 0

    # Only this call's window matters: its expansion is charged before the
    # 63/64 split and so lands in the boundary below. The filler asked a
    # fixed 600,000 here, a budget sized for the old schedule that the
    # boundary outgrows on EIP-8037 forks; asking for everything leaves the
    # clamp -- the actual subject -- in charge on every fork.
    second_call = Op.CALL(
        gas=Op.GAS,
        address=third_level,
        args_offset=window,
        args_size=window,
        ret_offset=window,
        ret_size=window,
        address_warm=False,
        account_new=False,
        new_memory_size=2 * window,
    )
    # The second level reports its result upward instead of storing it, so
    # the same program runs even when the caller used STATICCALL. Offset by
    # one, so a caller that receives nothing can tell that apart from a
    # frame that ran and saw its own callee fail.
    memory_after_call = 2 * window
    report_memory = max(memory_after_call, 0x20)
    report = Op.MSTORE(
        offset=0x0,
        value=Op.ADD(second_call, 1),
        new_memory_size=report_memory,
        old_memory_size=memory_after_call,
    ) + Op.RETURN(
        offset=0x0,
        size=0x20,
        new_memory_size=report_memory,
        old_memory_size=report_memory,
    )
    second = pre.deploy_contract(code=report)

    # Everything the second level runs before its call: the pushed offset
    # and the call itself. The rest is what it must still hold afterwards.
    before_call = Op.PUSH1[0].gas_cost(fork) + second_call.gas_cost(fork)
    retention_needed = report.gas_cost(fork) - before_call
    # A frame has to cover everything it runs, plus the 63 parts the 63/64
    # split hands down for every 1 it keeps back.
    boundary = report.gas_cost(fork) + 63 * retention_needed

    entry_call_gas = boundary if second_level == "survives" else boundary - 1
    # No window here: what the second level receives is this fixed operand,
    # so the entry's own memory costs cannot move the boundary.
    entry = pre.deploy_contract(
        code=Op.POP(
            call_opcode(
                gas=entry_call_gas,
                address=second,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(FLAG_SLOT, Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={FLAG_SLOT: SENTINEL},
    )

    # The transaction budget is deliberately not a boundary: maxing it out
    # leaves the entry's CALL operand as the only tuned value. The reservoir
    # is pinned to zero so a frame's state gas is charged against its own
    # gas_left, which is what the retention below is measured in.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=entry,
        state_gas_reservoir=0,
    )

    post = {
        # 1 == the second level reported back, 0 == it never got that far.
        # The seed would survive only if the entry itself had not run.
        entry: Account(
            storage={FLAG_SLOT: 1 if second_level == "survives" else 0}
        ),
        # Neither lower frame writes storage, which is what lets this run
        # under STATICCALL at all.
        second: Account(storage={}),
        third_level: Account(storage={}),
    }

    state_test(pre=pre, post=post, tx=tx)
