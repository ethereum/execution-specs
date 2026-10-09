"""
Test_call_contract_to_create_contract_oog.

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractOOGFiller.json
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
    ["state_tests/stInitCodeTest/CallContractToCreateContractOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_call_contract_to_create_contract_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_oog."""
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    # Source: lll
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 1 11 21)(CALL 0 (SLOAD 0) 0 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.CALL(
            gas=0x0,
            address=Op.SLOAD(key=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
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
