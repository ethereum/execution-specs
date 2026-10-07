"""
EIP-7979 test vectors.

The five programs given in the EIP, run byte-for-byte as callees. The caller
records the call's success flag; the gas each program consumes is checked
implicitly through the post-state root, and explicitly in ``test_gas.py``.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import SLOT_CALL_SUCCESS, TX_GAS_LIMIT, caller_recording_success
from .spec import ref_spec_7979

REFERENCE_SPEC_GIT_PATH = ref_spec_7979.git_path
REFERENCE_SPEC_VERSION = ref_spec_7979.version

pytestmark = pytest.mark.valid_from("EIP7979")


@pytest.mark.parametrize(
    "bytecode,success",
    [
        pytest.param(
            # PUSH1 0x04, CALLSUB, STOP, CALLDEST, RETURNSUB
            Op.PUSH1[0x04] + Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            True,
            id="simple_routine",
        ),
        pytest.param(
            # PUSH1 0x04, CALLSUB, STOP, CALLDEST, PUSH1 0x09, CALLSUB,
            # RETURNSUB, CALLDEST, RETURNSUB
            Op.PUSH1[0x04]
            + Op.CALLSUB
            + Op.STOP
            + Op.CALLDEST
            + Op.PUSH1[0x09]
            + Op.CALLSUB
            + Op.RETURNSUB
            + Op.CALLDEST
            + Op.RETURNSUB,
            True,
            id="two_levels_of_subroutines",
        ),
        pytest.param(
            # PUSH1 0xFF, CALLSUB, STOP, CALLDEST, RETURNSUB:
            # destination 255 is outside the 6-byte code.
            Op.PUSH1[0xFF] + Op.CALLSUB + Op.STOP + Op.CALLDEST + Op.RETURNSUB,
            False,
            id="failure_invalid_destination",
        ),
        pytest.param(
            # RETURNSUB with an empty return stack.
            Op.RETURNSUB,
            False,
            id="failure_empty_return_stack",
        ),
        pytest.param(
            # PUSH1 0x05, JUMP, CALLDEST, RETURNSUB, JUMPDEST, PUSH1 0x03,
            # CALLSUB: the CALLSUB is the last byte of code; RETURNSUB
            # returns to the implicit STOP past the end of the code.
            Op.PUSH1[0x05]
            + Op.JUMP
            + Op.CALLDEST
            + Op.RETURNSUB
            + Op.JUMPDEST
            + Op.PUSH1[0x03]
            + Op.CALLSUB,
            True,
            id="subroutine_at_end_of_code",
        ),
    ],
)
def test_eip_vectors(
    state_test: StateTestFiller,
    pre: Alloc,
    bytecode: Op,
    success: bool,
) -> None:
    """Run each EIP test vector verbatim and record whether it halted."""
    expected_hex = {
        "simple_routine": "6004b000b1b2",
        "two_levels_of_subroutines": "6004b000b16009b0b2b1b2",
        "failure_invalid_destination": "60ffb000b1b2",
        "failure_empty_return_stack": "b2",
        "subroutine_at_end_of_code": "600556b1b25b6003b0",
    }
    assert bytes(bytecode).hex() in expected_hex.values()

    callee = pre.deploy_contract(bytecode)
    caller = pre.deploy_contract(caller_recording_success(callee))
    tx = Transaction(sender=pre.fund_eoa(), to=caller, gas_limit=TX_GAS_LIMIT)
    post = {caller: Account(storage={SLOT_CALL_SUCCESS: int(success)})}
    state_test(pre=pre, post=post, tx=tx)
