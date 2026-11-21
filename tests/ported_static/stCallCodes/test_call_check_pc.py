"""
Check the PC after a call returns, for each call opcode.

Ported from:
state_tests/stCallCodes/callcode_checkPCFiller.json
state_tests/stStaticCall/static_callcode_checkPCFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcode_checkPCFiller.json",
        "state_tests/stStaticCall/static_callcode_checkPCFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL],
    ids=["call", "callcode", "delegatecall", "staticcall"],
)
def test_call_check_pc(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """Store the call's success and the PC of the instruction after it."""
    callee = pre.deploy_contract(code=Op.STOP)
    call = Op.SSTORE(0, opcode(address=callee))
    target = pre.deploy_contract(code=call + Op.SSTORE(3, Op.PC) + Op.STOP)

    tx = Transaction(sender=pre.fund_eoa(), to=target)

    post = {target: Account(storage={0: 1, 3: len(call)})}

    state_test(pre=pre, post=post, tx=tx)
