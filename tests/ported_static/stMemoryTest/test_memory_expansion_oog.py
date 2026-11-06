"""
Test that touching memory at a huge offset runs out of gas.

Ported from:
state_tests/stMemoryTest/calldatacopy_dejavuFiller.json
state_tests/stMemoryTest/codecopy_dejavuFiller.json
state_tests/stMemoryTest/extcodecopy_dejavuFiller.json
state_tests/stMemoryTest/log1_dejavuFiller.json
state_tests/stMemoryTest/log2_dejavuFiller.json
state_tests/stMemoryTest/log3_dejavuFiller.json
state_tests/stMemoryTest/log4_dejavuFiller.json
state_tests/stMemoryTest/mload_dejavuFiller.json
state_tests/stMemoryTest/mstore_dejavuFiller.json
state_tests/stMemoryTest/mstroe8_dejavuFiller.json
state_tests/stMemoryTest/sha3_dejavuFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

HUGE_OFFSET = 0xFFFFFFF
SIZE = 0xFF
INITIAL_RESULT = 0xDEAD
CANARY = 0xC0DE


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryTest/calldatacopy_dejavuFiller.json",
        "state_tests/stMemoryTest/codecopy_dejavuFiller.json",
        "state_tests/stMemoryTest/extcodecopy_dejavuFiller.json",
        "state_tests/stMemoryTest/log1_dejavuFiller.json",
        "state_tests/stMemoryTest/log2_dejavuFiller.json",
        "state_tests/stMemoryTest/log3_dejavuFiller.json",
        "state_tests/stMemoryTest/log4_dejavuFiller.json",
        "state_tests/stMemoryTest/mload_dejavuFiller.json",
        "state_tests/stMemoryTest/mstore_dejavuFiller.json",
        "state_tests/stMemoryTest/mstroe8_dejavuFiller.json",
        "state_tests/stMemoryTest/sha3_dejavuFiller.json",
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
@pytest.mark.parametrize(
    "code",
    [
        pytest.param(
            Op.CALLDATACOPY(HUGE_OFFSET, HUGE_OFFSET, SIZE),
            id="calldatacopy",
        ),
        pytest.param(
            Op.CODECOPY(HUGE_OFFSET, HUGE_OFFSET, SIZE), id="codecopy"
        ),
        pytest.param(
            Op.EXTCODECOPY(HUGE_OFFSET, HUGE_OFFSET, SIZE, SIZE),
            id="extcodecopy",
        ),
        pytest.param(Op.LOG1(HUGE_OFFSET, SIZE, SIZE), id="log1"),
        pytest.param(Op.LOG2(HUGE_OFFSET, SIZE, SIZE, SIZE), id="log2"),
        pytest.param(Op.LOG3(HUGE_OFFSET, SIZE, SIZE, SIZE, SIZE), id="log3"),
        pytest.param(
            Op.LOG4(HUGE_OFFSET, SIZE, SIZE, SIZE, SIZE, SIZE), id="log4"
        ),
        pytest.param(Op.MLOAD(HUGE_OFFSET), id="mload"),
        pytest.param(Op.MSTORE(HUGE_OFFSET, 0xF1), id="mstore"),
        pytest.param(Op.MSTORE8(HUGE_OFFSET, 0xF1), id="mstore8"),
        pytest.param(Op.SHA3(HUGE_OFFSET, SIZE), id="sha3"),
    ],
)
def test_memory_expansion_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    code: Bytecode,
) -> None:
    """Call a contract that expands memory past any gas budget."""
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=code + Op.STOP)
    caller = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.CALL(address=target))
        + Op.SSTORE(key=1, value=CANARY)
        + Op.STOP,
        storage={0: INITIAL_RESULT},
    )

    tx = Transaction(
        sender=sender,
        to=caller,
        protected=fork.supports_protected_txs(),
    )

    post = {caller: Account(storage={0: 0, 1: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
