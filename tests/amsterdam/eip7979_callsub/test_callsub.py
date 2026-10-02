"""
CALLSUB destination checks and the basic call/return round trip.

A CALLSUB whose destination is not a CALLDEST instruction is an exceptional
halt: a JUMPDEST, a byte inside PUSH data, a byte inside an EIP-8024
immediate, and any position outside the code all fail.
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


def test_call_and_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    CALLSUB enters the subroutine, RETURNSUB comes back to the instruction
    after the CALLSUB, and execution continues from there.
    """
    code, _ = program(
        lambda offset: Op.CALLSUB(offset)
        + Op.SSTORE(SLOT_MARKER_AFTER_RETURN, MARKER_AFTER_RETURN),
        subroutine_storing_marker(),
    )
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


def test_subroutine_called_twice(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A subroutine may be called any number of times; each call returns to
    its own call site.
    """

    def main(offset: int) -> Bytecode:
        return (
            Op.CALLSUB(offset)
            + Op.SSTORE(SLOT_MARKER_AFTER_RETURN, 1)
            + Op.CALLSUB(offset)
            + Op.SSTORE(
                SLOT_MARKER_AFTER_RETURN,
                Op.ADD(Op.SLOAD(SLOT_MARKER_AFTER_RETURN), 1),
            )
        )

    # The subroutine increments SLOT_MARKER on every entry.
    subroutine = (
        Op.CALLDEST
        + Op.SSTORE(SLOT_MARKER, Op.ADD(Op.SLOAD(SLOT_MARKER), 1))
        + Op.RETURNSUB
    )
    code, _ = program(main, subroutine)
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {
        contract: Account(
            storage={SLOT_MARKER: 2, SLOT_MARKER_AFTER_RETURN: 2}
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "callee_code",
    [
        pytest.param(
            # Destination is a JUMPDEST, not a CALLDEST.
            Op.PUSH1[0x04] + Op.CALLSUB + Op.STOP + Op.JUMPDEST + Op.RETURNSUB,
            id="jumpdest",
        ),
        pytest.param(
            # Destination 5 is the 0xB1 byte inside the PUSH1 immediate.
            Op.PUSH1[0x05] + Op.CALLSUB + Op.STOP + Op.PUSH1[0xB1] + Op.STOP,
            id="calldest_byte_in_push_data",
        ),
        pytest.param(
            # Destination 5 is the 0xB1 byte inside a DUPN immediate
            # (EIP-8024): the scan skips it, so it is not an instruction.
            Op.PUSH1[0x05] + Op.CALLSUB + Op.STOP + Op.DUPN[0xB1] + Op.STOP,
            id="calldest_byte_in_dupn_immediate",
        ),
        pytest.param(
            # Destination is one past the end of the code.
            Op.PUSH1[0x06] + Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            id="past_end_of_code",
        ),
        pytest.param(
            # Destination does not fit in 64 bits.
            Op.PUSH32[2**256 - 1]
            + Op.CALLSUB
            + Op.STOP
            + Op.CALLDEST
            + Op.RETURNSUB,
            id="destination_overflows_uint64",
        ),
        pytest.param(
            # Destination is the CALLSUB itself.
            Op.PUSH1[0x02] + Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            id="callsub_to_itself",
        ),
        pytest.param(
            # CALLSUB with an empty data stack.
            Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            id="stack_underflow",
        ),
    ],
)
def test_invalid_callsub_destination(
    state_test: StateTestFiller,
    pre: Alloc,
    callee_code: Op,
) -> None:
    """
    A CALLSUB to anything but a CALLDEST instruction is an exceptional
    halt.
    """
    callee = pre.deploy_contract(callee_code)
    caller = pre.deploy_contract(
        caller_recording_success(callee, gas=CALLEE_GAS)
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_CALL_SUCCESS: 0})}
    state_test(pre=pre, post=post, tx=tx)


def test_calldest_reached_by_fall_through(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLDEST executed in sequence is a no-op, like JUMPDEST."""
    code = (
        Op.CALLDEST
        + Op.CALLDEST
        + Op.SSTORE(SLOT_MARKER, MARKER_IN_SUBROUTINE)
        + Op.STOP
    )
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_MARKER: MARKER_IN_SUBROUTINE})}
    state_test(pre=pre, post=post, tx=tx)
