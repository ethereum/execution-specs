"""
Test_call_contract_to_create_contract_no_cash.

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractNoCashFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/CallContractToCreateContractNoCashFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_contract_to_create_contract_no_cash(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_no_cash."""
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    # Source: lll
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 100000 11 21)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x186A0, offset=0xB, size=0x15)
        )
        + Op.STOP,
        balance=10000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=100000,
    )

    post = {
        target: Account(nonce=1),
        sender: Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
