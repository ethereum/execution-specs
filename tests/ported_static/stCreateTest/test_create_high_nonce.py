"""
Test_create_high_nonce.

Ported from:
state_tests/stCreateTest/CREATE_HighNonceFiller.yml
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
    ["state_tests/stCreateTest/CREATE_HighNonceFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_create_high_nonce(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_high_nonce."""
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    # Source: yul
    # byzantium
    # {
    #   // initcode: { return(0, 1) }
    #   mstore(0, 0x60016000f3000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   sstore(0, create(0, 0, 5))
    #   sstore(1, 1)
    #
    #   let noOptimization := msize()
    # }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x60016000F3000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x5)
        )
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
        nonce=18446744073709551615,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=16777216,
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(storage={0: 0, 1: 1}, nonce=18446744073709551615),
        Address(
            0x04E9A8460199E670FFB592F93A2F74BDCB44B0BD
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
