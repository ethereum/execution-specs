"""
A test for (add 1 1) opcode result.

Ported from:
state_tests/stExample/add11_ymlFiller.yml
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
    ["state_tests/stExample/add11_ymlFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_add11_yml(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A test for (add 1 1) opcode result."""
    sender = pre.fund_eoa()

    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1)
    # }
    contract_0_code = Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP
    contract_0 = pre.deploy_contract(
        code=contract_0_code,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={0: 2},
            code=contract_0_code,
        ),
        sender: Account(storage={}, code=b"", nonce=1),
        pre.nonexistent_account(): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
