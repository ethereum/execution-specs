"""
Test_create_contract_sstore_during_init.

Ported from:
state_tests/stCreateTest/CREATE_ContractSSTOREDuringInitFiller.json
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
    ["state_tests/stCreateTest/CREATE_ContractSSTOREDuringInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_create_contract_sstore_during_init(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_contract_sstore_during_init."""
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x0, value=0xFF),
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={0: 255}
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
