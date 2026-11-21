"""
Execution of MAGIC code: it begins immediately after the header, positions
stay absolute (the header is part of the code), and the header is visible
to CODESIZE and CODECOPY.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import MARKER, SLOT_MARKER, SLOT_RESULT, TX_GAS_LIMIT, magic
from .spec import Spec, ref_spec_8337

REFERENCE_SPEC_GIT_PATH = ref_spec_8337.git_path
REFERENCE_SPEC_VERSION = ref_spec_8337.version

pytestmark = pytest.mark.valid_from("EIP8337")


def test_execution_begins_after_header(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    A MAGIC contract stores a marker. Were execution to begin at position
    0, the 0xEF byte would halt the frame before the store.
    """
    contract = pre.deploy_contract(magic(Op.SSTORE(SLOT_MARKER, MARKER)))
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_MARKER: MARKER})}
    state_test(pre=pre, post=post, tx=tx)


def test_codesize_includes_header(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CODESIZE reports the whole code, header included."""
    code = magic(Op.SSTORE(SLOT_RESULT, Op.CODESIZE))
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_RESULT: len(code)})}
    state_test(pre=pre, post=post, tx=tx)


def test_codecopy_sees_header(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CODECOPY from position 0 returns the header bytes."""
    code = magic(
        Op.CODECOPY(dest_offset=0, offset=0, size=Spec.HEADER_LENGTH)
        + Op.SSTORE(SLOT_RESULT, Op.MLOAD(0))
    )
    contract = pre.deploy_contract(code)
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    expected = int.from_bytes(Spec.MAGIC_HEADER.ljust(32, b"\x00"), "big")
    post = {contract: Account(storage={SLOT_RESULT: expected})}
    state_test(pre=pre, post=post, tx=tx)


def test_jump_and_call_positions_are_absolute(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    JUMP and CALLSUB destinations count from the start of the code,
    header included: the body jumps over a STOP to a JUMPDEST, then calls
    a subroutine, using absolute positions.
    """
    # Positions after the 3-byte header:
    #   3: PUSH1 7  5: JUMP  6: STOP  7: JUMPDEST  8: PUSH1 14  10: CALLSUB
    #  11: PUSH1 slot, SSTORE, STOP; then CALLDEST, PUSH1 marker, RETURNSUB
    main = (
        Op.PUSH1[7]
        + Op.JUMP
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0]  # patched to the subroutine position below
        + Op.CALLSUB
        + Op.PUSH1[SLOT_MARKER]
        + Op.SSTORE
        + Op.STOP
    )
    subroutine_pos = Spec.HEADER_LENGTH + len(main)
    main = (
        Op.PUSH1[7]
        + Op.JUMP
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[subroutine_pos]
        + Op.CALLSUB
        + Op.PUSH1[SLOT_MARKER]
        + Op.SSTORE
        + Op.STOP
    )
    subroutine = Op.CALLDEST + Op.PUSH1[MARKER] + Op.RETURNSUB
    contract = pre.deploy_contract(magic(main + subroutine))
    tx = Transaction(
        sender=pre.fund_eoa(), to=contract, gas_limit=TX_GAS_LIMIT
    )
    post = {contract: Account(storage={SLOT_MARKER: MARKER})}
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "call_opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
)
def test_magic_callee_in_every_call_context(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    A MAGIC callee runs from its entry point under every call opcode. It
    returns the marker through memory so STATICCALL frames can be checked.
    """
    callee = pre.deploy_contract(
        magic(Op.MSTORE(0, MARKER) + Op.RETURN(0, 32))
    )
    caller = pre.deploy_contract(
        Op.SSTORE(
            SLOT_RESULT,
            call_opcode(
                gas=200_000, address=callee, ret_offset=0, ret_size=32
            ),
        )
        + Op.SSTORE(SLOT_MARKER, Op.MLOAD(0))
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_RESULT: 1, SLOT_MARKER: MARKER})}
    state_test(pre=pre, post=post, tx=tx)


def test_invalid_magic_code_in_pre_state_still_runs(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Validation happens only at CREATE. MAGIC code placed directly in state
    (as tests, or a future irregular state change, can do) is executed
    with the ordinary runtime checks, so a body that would fail validation
    simply halts at runtime.
    """
    # POP on an empty stack: invalid code, halts at runtime.
    callee = pre.deploy_contract(magic(Op.POP + Op.STOP))
    caller = pre.deploy_contract(
        Op.SSTORE(SLOT_RESULT, Op.CALL(gas=200_000, address=callee))
    )
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_RESULT: 0})}
    state_test(pre=pre, post=post, tx=tx)
