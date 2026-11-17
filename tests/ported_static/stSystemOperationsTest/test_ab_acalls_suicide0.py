"""
Test_ab_acalls_suicide0.

Ported from:
state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json

@manually-enhanced: Do not overwrite. Addresses unpinned.
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


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/ABAcallsSuicide0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_ab_acalls_suicide0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Call B with value, then SELFDESTRUCT to B; B calls back to A.

    B stores one plus the result of its call back into A.
    """
    sender = pre.fund_eoa()

    b_value = Op.ADD(1, Op.CALL(gas=50000, address=Op.CALLER, value=0x17))
    contract_b = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=b_value) + Op.STOP,
        balance=23,
    )
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.CALL(gas=100000, address=contract_b, value=0x18),
        )
        + Op.SELFDESTRUCT(address=contract_b)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(sender=sender, to=contract_a)

    # B's store key is the offset of its PC, right after the value.
    post = {contract_b: Account(storage={len(b_value): 1})}

    state_test(pre=pre, post=post, tx=tx)
