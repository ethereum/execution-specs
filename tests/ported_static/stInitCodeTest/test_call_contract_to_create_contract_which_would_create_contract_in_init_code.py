"""
Test_call_contract_to_create_contract_which_would_create_contract_in_ini...

Ported from:
state_tests/stInitCodeTest/CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json
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
        "state_tests/stInitCodeTest/CallContractToCreateContractWhichWouldCreateContractInInitCodeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_call_contract_to_create_contract_which_would_create_contract_in_init_code(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_contract_to_create_contract_which_would_create_contract_i..."""  # noqa: E501
    sender = pre.fund_eoa()

    # Source: lll
    # {(MSTORE 0 0x600c600055602060406000f0)(CREATE 0 20 12)}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600C600055602060406000F0)
        + Op.CREATE(value=0x0, offset=0x14, size=0xC)
        + Op.STOP,
        balance=1,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
    )

    created = compute_create_address(address=contract_0, nonce=1)
    post = {
        contract_0: Account(balance=1, nonce=2),
        sender: Account(nonce=1),
        created: Account(storage={0: 12}, nonce=2, code=b""),
        compute_create_address(address=created, nonce=1): Account(
            nonce=1, code=b""
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
