"""
Test POP.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/popFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/popFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "code, storage",
    [
        pytest.param(
            Op.PUSH1[0x2] + Op.PUSH1[0x3] + Op.POP(0x4) + Op.SSTORE,
            {0: SENTINEL, 3: 2, 4: SENTINEL},
            id="pop1",
        ),
        pytest.param(
            Op.POP + Op.PUSH1[0x2] + Op.SSTORE(key=0x4, value=0x3),
            {0: SENTINEL, 4: SENTINEL},
            id="pop2",
        ),
    ],
)
def test_pop(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: dict,
) -> None:
    """Pop a stack item, or fail on an empty stack."""
    contract = pre.deploy_contract(
        code=code, storage={0: SENTINEL, 4: SENTINEL}
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
