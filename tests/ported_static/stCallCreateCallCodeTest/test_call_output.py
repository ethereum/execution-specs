"""
Check the output memory after call.

Ported from:
state_tests/stCallCreateCallCodeTest/callOutput1Filler.json
state_tests/stCallCreateCallCodeTest/callOutput2Filler.json
state_tests/stCallCreateCallCodeTest/callOutput3Filler.json
state_tests/stCallCreateCallCodeTest/callOutput3FailFiller.json
state_tests/stCallCreateCallCodeTest/callOutput3partialFiller.json
state_tests/stCallCreateCallCodeTest/callOutput3partialFailFiller.json
state_tests/stCallCreateCallCodeTest/callcodeOutput1Filler.json
state_tests/stCallCreateCallCodeTest/callcodeOutput2Filler.json
state_tests/stCallCreateCallCodeTest/callcodeOutput3Filler.json
state_tests/stCallCreateCallCodeTest/callcodeOutput3FailFiller.json
state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFiller.json
state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFailFiller.json
state_tests/stDelegatecallTestHomestead/callOutput1Filler.json
state_tests/stDelegatecallTestHomestead/callOutput2Filler.json
state_tests/stDelegatecallTestHomestead/callOutput3Filler.json
state_tests/stDelegatecallTestHomestead/callOutput3partialFiller.json
state_tests/stDelegatecallTestHomestead/callOutput3partialFailFiller.json
state_tests/stDelegatecallTestHomestead/callcodeOutput3Filler.json

@manually-enhanced: Do not overwrite. Opcode, memory-window and callee-failure
fillers merged.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

MEMORY_WORD = (
    0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6
)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCreateCallCodeTest/callOutput1Filler.json",
        "state_tests/stCallCreateCallCodeTest/callOutput2Filler.json",
        "state_tests/stCallCreateCallCodeTest/callOutput3Filler.json",
        "state_tests/stCallCreateCallCodeTest/callOutput3FailFiller.json",
        "state_tests/stCallCreateCallCodeTest/callOutput3partialFiller.json",
        "state_tests/stCallCreateCallCodeTest/callOutput3partialFailFiller.json",  # noqa: E501
        "state_tests/stCallCreateCallCodeTest/callcodeOutput1Filler.json",
        "state_tests/stCallCreateCallCodeTest/callcodeOutput2Filler.json",
        "state_tests/stCallCreateCallCodeTest/callcodeOutput3Filler.json",
        "state_tests/stCallCreateCallCodeTest/callcodeOutput3FailFiller.json",
        "state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFiller.json",  # noqa: E501
        "state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFailFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/callOutput1Filler.json",
        "state_tests/stDelegatecallTestHomestead/callOutput2Filler.json",
        "state_tests/stDelegatecallTestHomestead/callOutput3Filler.json",
        "state_tests/stDelegatecallTestHomestead/callOutput3partialFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/callOutput3partialFailFiller.json",  # noqa: E501
        "state_tests/stDelegatecallTestHomestead/callcodeOutput3Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode",
    [Op.CALL, Op.CALLCODE, Op.DELEGATECALL],
    ids=["call", "callcode", "delegatecall"],
)
@pytest.mark.parametrize(
    "args_size, ret_size",
    [(0, 0), (0x20, 0), (0, 0x20), (0, 0xA)],
    ids=["output1", "output2", "output3", "output3partial"],
)
@pytest.mark.parametrize("callee_fails", [False, True], ids=["ok", "fail"])
def test_call_output(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    args_size: int,
    ret_size: int,
    callee_fails: bool,
) -> None:
    """
    Call a callee that returns no data over a filled memory word.

    The memory word must be unchanged after the call, whether the callee
    succeeds or fails on a stack underflow.
    """
    sender = pre.fund_eoa()

    callee_code = Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1))
    if callee_fails:
        callee_code = Op.ADD + callee_code
    callee = pre.deploy_contract(code=callee_code)
    target = pre.deploy_contract(
        code=Op.MSTORE(0, MEMORY_WORD)
        + Op.SSTORE(
            1, opcode(address=callee, args_size=args_size, ret_size=ret_size)
        )
        + Op.SSTORE(0, Op.MLOAD(0))
        + Op.STOP,
    )

    tx = Transaction(sender=sender, to=target)

    callee_storage: dict = {}
    if opcode == Op.CALL and not callee_fails:
        callee_storage = {0: 2}
    post = {
        target: Account(storage={0: MEMORY_WORD, 1: int(not callee_fails)}),
        callee: Account(storage=callee_storage),
    }

    state_test(pre=pre, post=post, tx=tx)
