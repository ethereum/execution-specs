"""
Test_create_name_registrator_value_too_high.

Ported from:
state_tests/stSystemOperationsTest/createNameRegistratorValueTooHighFiller.json
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
        "state_tests/stSystemOperationsTest/createNameRegistratorValueTooHighFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_name_registrator_value_too_high(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_name_registrator_value_too_high."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 1000000000000000001 3 29) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F3006000355415600957005B60203560003555,
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE(value=0xDE0B6B3A7640001, offset=0x3, size=0x1D),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=300000,
    )

    post = {
        compute_create_address(
            address=contract_0, nonce=1
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
