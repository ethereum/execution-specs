"""
Test_non_zero_value_suicide.

Ported from:
state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDEFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stNonZeroCallsTest/NonZeroValue_SUICIDEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_non_zero_value_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_non_zero_value_suicide."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (SELFDESTRUCT 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b) }
    contract_0_code = (
        Op.SELFDESTRUCT(address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
        + Op.STOP
    )
    contract_0 = pre.deploy_contract(
        code=contract_0_code,
        balance=1,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(
            storage={},
            code=contract_0_code,
            balance=0,
            nonce=1,
        ),
        Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B): Account(
            balance=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
