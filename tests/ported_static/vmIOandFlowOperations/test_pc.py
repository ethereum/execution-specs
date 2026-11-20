"""
Test PC.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/pcFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SENTINEL = 0x0BAD


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmIOandFlowOperations/pcFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "code, storage",
    [
        pytest.param(Op.SSTORE(0, Op.PC) + Op.STOP, {0: 0}, id="pc1"),
        pytest.param(
            Op.SSTORE(0, 0xFF) + Op.SSTORE(1, Op.PC) + Op.STOP,
            {0: 0xFF, 1: 5},
            id="pc2",
        ),
    ],
)
def test_pc(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: dict,
) -> None:
    """Store the program counter."""
    contract = pre.deploy_contract(code=code, storage={0: SENTINEL})
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
