"""
Test_call_contract_to_create_contract_and_call_it_oog.

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractAndCallItOOGFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stInitCodeTest/CallContractToCreateContractAndCallItOOGFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_contract_to_create_contract_and_call_it_oog(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_and_call_it_oog."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # Source: lll
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 1 11 21)(CALL 1000 (SLOAD 0) 0 0 0 0 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.CALL(
            gas=0x3E8,
            address=Op.SLOAD(key=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=1000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=2203000 if fork >= Amsterdam else 203000,
    )

    post = {
        contract_0: Account(
            storage={
                0: compute_create_address(address=contract_0, nonce=1),
            },
            nonce=2,
        ),
        sender: Account(nonce=1),
        compute_create_address(address=contract_0, nonce=1): Account(
            storage={0: 12}, balance=1, nonce=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
