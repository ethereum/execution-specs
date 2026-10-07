"""
RETURNSUB and the return stack: underflow, the 1024-entry limit, and the
frame boundary.
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
    SLOT_CALL_SUCCESS,
    SLOT_MARKER,
    TX_GAS_LIMIT,
    caller_recording_success,
    program,
)
from .spec import Spec, ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

pytestmark = pytest.mark.valid_from("EIP7979")


@pytest.mark.parametrize(
    "callee_code",
    [
        pytest.param(Op.RETURNSUB, id="first_instruction"),
        pytest.param(
            # Falling into a subroutine pushes no return address.
            Op.CALLDEST + Op.RETURNSUB,
            id="after_fall_through_into_calldest",
        ),
        pytest.param(
            # One CALLSUB, two RETURNSUBs: the second underflows.
            Op.PUSH1[0x04]
            + Op.CALLSUB
            + Op.RETURNSUB
            + Op.CALLDEST
            + Op.RETURNSUB,
            id="second_returnsub_after_one_callsub",
        ),
    ],
)
def test_returnsub_underflow(
    state_test: StateTestFiller,
    pre: Alloc,
    callee_code: Op,
) -> None:
    """RETURNSUB with an empty return stack is an exceptional halt."""
    callee = pre.deploy_contract(callee_code)
    caller = pre.deploy_contract(
        caller_recording_success(callee, gas=CALLEE_GAS)
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_CALL_SUCCESS: 0})}
    state_test(pre=pre, post=post, tx=tx)


def counted_recursion(depth: int) -> Bytecode:
    """
    Return a program whose subroutine calls itself `depth` times, using a
    counter on the data stack, then stores 1 at ``SLOT_MARKER``.

    The return stack reaches `depth` + 1 entries: one for the outer call
    plus one per recursive call.
    """

    def main(offset: int) -> Bytecode:
        return (
            Op.PUSH2[depth]
            + Op.CALLSUB(offset)
            + Op.POP
            + Op.SSTORE(SLOT_MARKER, 1)
        )

    def subroutine_for(offset: int, done: int) -> Bytecode:
        return (
            Op.CALLDEST
            # if counter == 0: jump to done
            + Op.DUP1
            + Op.ISZERO
            + Op.PUSH1[done]
            + Op.JUMPI
            # counter -= 1
            + Op.PUSH1[1]
            + Op.SWAP1
            + Op.SUB
            # recurse
            + Op.PUSH1[offset]
            + Op.CALLSUB
            + Op.RETURNSUB
            + Op.JUMPDEST  # done:
            + Op.RETURNSUB
        )

    offset = len(main(0)) + 1
    # `done` is the JUMPDEST just before the last RETURNSUB.
    done = offset + len(subroutine_for(0, 0)) - 2
    code = main(offset) + Op.STOP + subroutine_for(offset, done)
    assert len(code) < 256
    return code


@pytest.mark.parametrize(
    "depth,success",
    [
        pytest.param(Spec.RETURN_STACK_LIMIT - 1, True, id="at_limit"),
        pytest.param(Spec.RETURN_STACK_LIMIT, False, id="over_limit"),
    ],
)
def test_return_stack_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    depth: int,
    success: bool,
) -> None:
    """
    The return stack holds at most 1024 addresses: recursion 1023 deep
    (1024 entries) completes, one level deeper halts.
    """
    callee = pre.deploy_contract(counted_recursion(depth))
    caller = pre.deploy_contract(
        caller_recording_success(callee, gas=CALLEE_GAS)
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {
        caller: Account(storage={SLOT_CALL_SUCCESS: int(success)}),
        callee: Account(storage={SLOT_MARKER: int(success)}),
    }
    state_test(pre=pre, post=post, tx=tx)


def test_unbounded_recursion_halts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Recursion with no base case halts on return-stack overflow, not on
    running out of gas.
    """
    # PUSH1 4, CALLSUB, STOP, CALLDEST, PUSH1 4, CALLSUB, RETURNSUB
    callee_code = (
        Op.PUSH1[0x04]
        + Op.CALLSUB
        + Op.STOP
        + Op.CALLDEST
        + Op.PUSH1[0x04]
        + Op.CALLSUB
        + Op.RETURNSUB
    )
    callee = pre.deploy_contract(callee_code)
    # Record the gas left after the call: an overflow halt consumes only
    # the callee's gas, so the caller keeps roughly what it withheld.
    caller_code = Op.SSTORE(
        SLOT_CALL_SUCCESS, Op.CALL(gas=CALLEE_GAS, address=callee)
    ) + Op.SSTORE(SLOT_MARKER, Op.GT(Op.GAS, 100_000))
    caller = pre.deploy_contract(caller_code)
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_CALL_SUCCESS: 0, SLOT_MARKER: 1})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
)
@pytest.mark.parametrize(
    "callee_code,callee_success",
    [
        pytest.param(Op.RETURNSUB, 0, id="callee_underflows_own_return_stack"),
        pytest.param(
            Op.PUSH1[0x04] + Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            1,
            id="callee_uses_own_return_stack",
        ),
    ],
)
def test_return_stack_is_per_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    callee_code: Op,
    callee_success: int,
) -> None:
    """
    Each message frame has its own return stack. A callee starts with an
    empty one even while the caller's holds a return address, and the
    caller's return address survives the nested call.
    """
    callee = pre.deploy_contract(callee_code)

    def main(offset: int) -> Bytecode:
        # Call the subroutine, which performs the nested call; then store
        # a marker to prove RETURNSUB brought us back here.
        return Op.CALLSUB(offset) + Op.SSTORE(SLOT_MARKER, 1)

    subroutine = (
        Op.CALLDEST
        + Op.SSTORE(
            SLOT_CALL_SUCCESS, call_opcode(gas=CALLEE_GAS, address=callee)
        )
        + Op.RETURNSUB
    )
    code, _ = program(main, subroutine)
    caller = pre.deploy_contract(code)
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {
        caller: Account(
            storage={SLOT_CALL_SUCCESS: callee_success, SLOT_MARKER: 1}
        )
    }
    state_test(pre=pre, post=post, tx=tx)
