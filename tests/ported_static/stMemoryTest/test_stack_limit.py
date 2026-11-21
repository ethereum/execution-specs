"""
Test a loop that grows the stack to a peak just below, at and above the limit.

Ported from:
state_tests/stMemoryTest/stackLimitGas_1023Filler.json
state_tests/stMemoryTest/stackLimitGas_1024Filler.json
state_tests/stMemoryTest/stackLimitGas_1025Filler.json
state_tests/stMemoryTest/stackLimitPush31_1023Filler.json
state_tests/stMemoryTest/stackLimitPush31_1024Filler.json
state_tests/stMemoryTest/stackLimitPush31_1025Filler.json
state_tests/stMemoryTest/stackLimitPush32_1023Filler.json
state_tests/stMemoryTest/stackLimitPush32_1024Filler.json
state_tests/stMemoryTest/stackLimitPush32_1025Filler.json
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

CANARY = 0xC0DE
# Items the loop body holds above the pushed items at its deepest point.
LOOP_OVERHEAD = 2


@pytest.mark.ported_from(
    [
        "state_tests/stMemoryTest/stackLimitGas_1023Filler.json",
        "state_tests/stMemoryTest/stackLimitGas_1024Filler.json",
        "state_tests/stMemoryTest/stackLimitGas_1025Filler.json",
        "state_tests/stMemoryTest/stackLimitPush31_1023Filler.json",
        "state_tests/stMemoryTest/stackLimitPush31_1024Filler.json",
        "state_tests/stMemoryTest/stackLimitPush31_1025Filler.json",
        "state_tests/stMemoryTest/stackLimitPush32_1023Filler.json",
        "state_tests/stMemoryTest/stackLimitPush32_1024Filler.json",
        "state_tests/stMemoryTest/stackLimitPush32_1025Filler.json",
    ],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize("stack_peak", [1023, 1024, 1025])
@pytest.mark.parametrize(
    "item",
    [
        pytest.param(Op.GAS, id="gas"),
        pytest.param(
            Op.PUSH31[
                0x102030405060708090A0102030405060708090A0102030405060708090A01
            ],
            id="push31",
        ),
        pytest.param(
            Op.PUSH32[
                0x102030405060708090A0102030405060708090A0102030405060708090A0102
            ],
            id="push32",
        ),
    ],
)
def test_stack_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    item: Bytecode,
    stack_peak: int,
) -> None:
    """Push one item per iteration, then store a canary after the loop."""
    sender = pre.fund_eoa()

    iterations = stack_peak - LOOP_OVERHEAD
    setup = Op.MSTORE(offset=0, value=iterations)
    loop = (
        Op.JUMPDEST
        + item
        + Op.MSTORE(offset=0, value=Op.SUB(Op.MLOAD(offset=0), 1))
        + Op.JUMPI(pc=len(setup), condition=Op.MLOAD(offset=0))
    )
    target = pre.deploy_contract(
        code=setup + loop + Op.SSTORE(key=0, value=CANARY) + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        protected=fork.supports_protected_txs(),
    )

    overflows = stack_peak > fork.max_stack_height()
    post = {target: Account(storage={} if overflows else {0: CANARY})}

    state_test(pre=pre, post=post, tx=tx)
