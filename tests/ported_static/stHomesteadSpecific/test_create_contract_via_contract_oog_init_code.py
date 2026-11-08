"""
Test_create_contract_via_contract_oog_init_code.

Ported from:
state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stHomesteadSpecific/createContractViaContractOOGInitCodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_contract_via_contract_oog_init_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_contract_via_contract_oog_init_code."""
    sender = pre.fund_eoa(amount=0x10C8E0)

    # Source: lll
    # { (MSTORE 0 0x602060406000f0600c600055)(CREATE 0 20 12)}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x602060406000F0600C600055)
        + Op.CREATE(value=0x0, offset=0x14, size=0xC)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=105044,
    )

    post = {
        compute_create_address(
            address=compute_create_address(address=contract_0, nonce=1),
            nonce=0,
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
