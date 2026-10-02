"""
CALLDEST as a jump destination: call elimination.

A JUMP or JUMPI may land on a CALLDEST. Doing so enters the subroutine
without pushing a return address, so the subroutine's RETURNSUB returns to
the original caller. Compilers use this for tail calls and shared epilogues.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import (
    CALLEE_GAS,
    MARKER_AFTER_RETURN,
    MARKER_IN_SUBROUTINE,
    SLOT_CALL_SUCCESS,
    SLOT_MARKER,
    SLOT_MARKER_AFTER_RETURN,
    TX_GAS_LIMIT,
    caller_recording_success,
    program,
    subroutine_storing_marker,
)
from .spec import ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

pytestmark = pytest.mark.valid_from("EIP7979")


@pytest.mark.parametrize("conditional", [False, True], ids=["jump", "jumpi"])
def test_jump_to_calldest(
    state_test: StateTestFiller,
    pre: Alloc,
    conditional: bool,
) -> None:
    """
    JUMP and JUMPI accept a CALLDEST as destination. The subroutine body
    runs; its RETURNSUB is not reached because the body ends with STOP.
    """
    subroutine = (
        Op.CALLDEST + Op.SSTORE(SLOT_MARKER, MARKER_IN_SUBROUTINE) + Op.STOP
    )

    def main(offset: int) -> Bytecode:
        if conditional:
            return Op.JUMPI(offset, 1)
        return Op.JUMP(offset)

    code, _ = program(main, subroutine)
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_MARKER: MARKER_IN_SUBROUTINE})}
    state_test(pre=pre, post=post, tx=tx)


def test_tail_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Subroutine `f` ends by jumping to subroutine `g` instead of calling it.
    `g`'s RETURNSUB returns directly to `f`'s caller, and the return stack
    never holds more than one address.
    """

    def main(f_offset: int) -> Bytecode:
        return Op.CALLSUB(f_offset) + Op.SSTORE(
            SLOT_MARKER_AFTER_RETURN, MARKER_AFTER_RETURN
        )

    # Layout: main, STOP, f, g. `g` is the marker-storing subroutine.
    g = subroutine_storing_marker()

    def f_for(g_offset: int) -> Bytecode:
        return Op.CALLDEST + Op.JUMP(g_offset)

    f_offset = len(main(0)) + 1
    g_offset = f_offset + len(f_for(0))
    code = main(f_offset) + Op.STOP + f_for(g_offset) + g
    assert len(code) < 256

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={
                SLOT_MARKER: MARKER_IN_SUBROUTINE,
                SLOT_MARKER_AFTER_RETURN: MARKER_AFTER_RETURN,
            }
        )
    }
    state_test(pre=pre, post=post, tx=tx)


def test_returnsub_after_unframed_jump_halts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Entering a subroutine by JUMP from top-level code pushes no return
    address, so its RETURNSUB underflows.
    """
    callee_code = (
        Op.PUSH1[0x04] + Op.JUMP + Op.STOP + Op.CALLDEST + Op.RETURNSUB
    )
    callee = pre.deploy_contract(callee_code)
    caller = pre.deploy_contract(
        caller_recording_success(callee, gas=CALLEE_GAS)
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_CALL_SUCCESS: 0})}
    state_test(pre=pre, post=post, tx=tx)


def test_mutual_recursion_at_constant_depth(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Two subroutines that jump to each other run a loop of 2000 iterations
    at constant return-stack depth, well past the 1024 limit that calls
    would hit. The counter lives on the data stack.
    """
    iterations = 2000

    def main(a_offset: int) -> Bytecode:
        return (
            Op.PUSH2[iterations]
            + Op.CALLSUB(a_offset)
            + Op.POP
            + Op.SSTORE(SLOT_MARKER, 1)
        )

    def a_for(b_offset: int, done: int) -> Bytecode:
        # a: if counter == 0 return; counter -= 1; jump b
        return (
            Op.CALLDEST
            + Op.DUP1
            + Op.ISZERO
            + Op.PUSH1[done]
            + Op.JUMPI
            + Op.PUSH1[1]
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1[b_offset]
            + Op.JUMP
            + Op.JUMPDEST  # done:
            + Op.RETURNSUB
        )

    def b_for(a_offset: int) -> Bytecode:
        # b: jump a
        return Op.CALLDEST + Op.PUSH1[a_offset] + Op.JUMP

    a_offset = len(main(0)) + 1
    b_offset = a_offset + len(a_for(0, 0))
    done = b_offset - 2
    code = main(a_offset) + Op.STOP + a_for(b_offset, done) + b_for(a_offset)
    assert len(code) < 256

    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_MARKER: 1})}
    state_test(pre=pre, post=post, tx=tx)
