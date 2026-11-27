"""
Test_stack_under_flow_contract_creation.

Ported from:
state_tests/stInitCodeTest/StackUnderFlowContractCreationFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stInitCodeTest/StackUnderFlowContractCreationFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_stack_under_flow_contract_creation(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_stack_under_flow_contract_creation."""
    sender = pre.fund_eoa(amount=0xAE9F7BCC00)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.PUSH1[0x0] + Op.CALL,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
