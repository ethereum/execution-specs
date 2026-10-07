"""Shared bytecode builders for the EIP-7979 tests."""

from typing import Callable, Tuple

from execution_testing import Address, Bytecode, Op

# Storage slots used by callers to record what they observed.
SLOT_CALL_SUCCESS = 0
SLOT_MARKER = 1
SLOT_MARKER_AFTER_RETURN = 2

MARKER_IN_SUBROUTINE = 0xA1
MARKER_AFTER_RETURN = 0xB2

# Gas handed to a callee so that its exceptional halts cannot starve the
# caller, which still has to record the outcome.
CALLEE_GAS = 500_000

# Gas limit for the transactions in these tests.
TX_GAS_LIMIT = 1_000_000


def caller_recording_success(
    callee: Address, gas: int = CALLEE_GAS
) -> Bytecode:
    """
    Return caller code that CALLs `callee` and stores the success flag
    at ``SLOT_CALL_SUCCESS``.

    An exceptional halt in the callee yields 0, normal completion yields 1.
    """
    return Op.SSTORE(SLOT_CALL_SUCCESS, Op.CALL(gas=gas, address=callee))


def subroutine_storing_marker() -> Bytecode:
    """
    Return a subroutine: CALLDEST, store ``MARKER_IN_SUBROUTINE`` at
    ``SLOT_MARKER``, RETURNSUB.
    """
    return (
        Op.CALLDEST
        + Op.SSTORE(SLOT_MARKER, MARKER_IN_SUBROUTINE)
        + Op.RETURNSUB
    )


def program(
    main_for: Callable[[int], Bytecode], subroutine: Bytecode
) -> Tuple[Bytecode, int]:
    """
    Assemble ``main_for(offset) + STOP + subroutine`` where `offset` is the
    code offset of the subroutine.

    `main_for` builds the main code given the subroutine's offset; it must
    produce code of the same length for any offset below 256 (use PUSH1).
    Returns the whole program and the offset.
    """
    offset = len(main_for(0)) + 1  # + STOP
    assert offset < 256, "keep test programs under 256 bytes"
    main = main_for(offset)
    assert len(main) == len(main_for(0))
    return main + Op.STOP + subroutine, offset
