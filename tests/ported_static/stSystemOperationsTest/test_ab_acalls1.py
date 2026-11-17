"""
Test_ab_acalls1.

Ported from:
state_tests/stSystemOperationsTest/ABAcalls1Filler.json

@manually-enhanced: Do not overwrite. Addresses unpinned, Prague cap dropped.
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

GAS_RESERVE = 100_000


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/ABAcalls1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_ab_acalls1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Recurse between A and B with value, each keeping a gas reserve.

    Every level stores its call result at a PC-derived slot; the top
    levels keep enough reserve to store that their callee succeeded.
    """
    sender = pre.fund_eoa()

    b_value = Op.ADD(
        1,
        Op.CALL(
            gas=Op.SUB(Op.GAS, GAS_RESERVE), address=Op.CALLER, value=0x17
        ),
    )
    contract_b = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=b_value) + Op.STOP,
        balance=23,
    )
    a_value = Op.CALL(
        gas=Op.SUB(Op.GAS, GAS_RESERVE), address=contract_b, value=0x18
    )
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(key=Op.PC, value=a_value) + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(sender=sender, to=contract_a)

    # Each store's key is the offset of its PC, right after the value.
    post = {
        contract_a: Account(storage={len(a_value): 1}),
        contract_b: Account(storage={len(b_value): 2}),
    }

    state_test(pre=pre, post=post, tx=tx)
