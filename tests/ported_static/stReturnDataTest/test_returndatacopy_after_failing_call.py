"""
Test that RETURNDATACOPY past the end of an empty return buffer fails.

Ported from:
state_tests/stReturnDataTest/returndatacopy_after_failing_callcodeFiller.json
state_tests/stReturnDataTest/returndatacopy_after_failing_delegatecallFiller.json
state_tests/stReturnDataTest/returndatacopy_after_failing_staticcallFiller.json

@manually-enhanced: Do not overwrite. Three fillers parametrized by call
opcode (plus CALL) and by how the callee fails: an INVALID callee instead of
a bare REVERT that only failed through a stack underflow, or a callee that
would return 32 bytes but is given no gas.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    Opcode,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Enough for the INVALID callee to start; it consumes all of it.
CALLEE_GAS = 10_000
PRESET_VALUE = 0xFFFFFFFFFFFF


@pytest.mark.ported_from(
    [
        "state_tests/stReturnDataTest/returndatacopy_after_failing_callcodeFiller.json",  # noqa: E501
        "state_tests/stReturnDataTest/returndatacopy_after_failing_delegatecallFiller.json",  # noqa: E501
        "state_tests/stReturnDataTest/returndatacopy_after_failing_staticcallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.CALLCODE, id="callcode"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(Op.STATICCALL, id="staticcall"),
    ],
)
@pytest.mark.parametrize("failure", ["invalid", "out_of_gas"])
def test_returndatacopy_after_failing_call(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Opcode,
    failure: str,
) -> None:
    """
    Copy 32 bytes of return data after a call whose callee failed.

    The callee either hits INVALID, or would return 32 bytes but is called
    with no gas. Either way the failed call leaves the return data buffer
    empty, so RETURNDATACOPY reads out of bounds and halts the frame,
    reverting the whole transaction: the pre-set storage value survives.
    """
    if failure == "invalid":
        callee = pre.deploy_contract(code=Op.INVALID)
        call = opcode(gas=CALLEE_GAS, address=callee)
    else:
        callee = pre.deploy_contract(
            code=Op.MSTORE(offset=0, value=Op.CALLER)
            + Op.RETURN(offset=0, size=32)
        )
        call = opcode(gas=0, address=callee)

    target = pre.deploy_contract(
        code=Op.POP(call)
        + Op.RETURNDATACOPY(dest_offset=0, offset=0, size=32)
        + Op.SSTORE(key=0, value=Op.MLOAD(offset=0))
        + Op.STOP,
        storage={0: PRESET_VALUE},
    )

    tx = Transaction(sender=pre.fund_eoa(), to=target)

    post = {target: Account(storage={0: PRESET_VALUE})}

    state_test(pre=pre, post=post, tx=tx)
