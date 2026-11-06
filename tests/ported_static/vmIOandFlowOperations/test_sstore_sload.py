"""
Test SSTORE and SLOAD.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/sstore_sloadFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/sstore_sloadFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "code, storage",
    [
        pytest.param(
            Op.SSTORE(0, 0xFF)
            + Op.SSTORE(10, 0xEE)
            + Op.SSTORE(20, Op.SLOAD(0))
            + Op.STOP,
            {0: 0xFF, 10: 0xEE, 20: 0xFF},
            id="sstore_sload_3",
        ),
        pytest.param(
            Op.SSTORE(0, 0xFF)
            + Op.SSTORE(10, 0xEE)
            + Op.SSTORE(20, Op.SLOAD(100))
            + Op.STOP,
            {0: 0xFF, 10: 0xEE, 20: 0},
            id="sstore_sload_noinit",
        ),
        pytest.param(
            Op.SSTORE(0, 0xFF)
            + Op.SSTORE(1, 0xEE)
            + Op.SSTORE(2, 0xDD)
            + Op.SSTORE(10, Op.SLOAD(1))
            + Op.SSTORE(20, Op.SLOAD(2))
            + Op.STOP,
            {0: 0xFF, 1: 0xEE, 2: 0xDD, 10: 0xEE, 20: 0xDD},
            id="sstore_sload_4",
        ),
    ],
)
def test_sstore_sload(
    state_test: StateTestFiller,
    pre: Alloc,
    code: Bytecode,
    storage: dict,
) -> None:
    """Store values and copy them between slots with SLOAD."""
    contract = pre.deploy_contract(
        code=code, storage={0: SENTINEL, 20: SENTINEL}
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    post = {contract: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)
