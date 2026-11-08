"""
Test_delegatecall_in_initcode_to_empty_contract.

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json
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
        "state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToEmptyContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_delegatecall_in_initcode_to_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegatecall_in_initcode_to_empty_contract."""
    sender = pre.fund_eoa(amount=0x2386F26FC10000)

    # Source: lll
    # { (MSTORE 0 0x604060006040600073945304eb96065b2a98b57a48a06ae28d285a71b5620186) (MSTORE 32 0xa0f4600055000000000000000000000000000000000000000000000000000000) (CREATE 1 0 64) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x604060006040600073945304EB96065B2A98B57A48A06AE28D285A71B5620186,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xA0F4600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CREATE(value=0x1, offset=0x0, size=0x40)
        + Op.STOP,
        balance=10000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=453081,
    )

    post = {
        compute_create_address(address=contract_0, nonce=1): Account(
            storage={0: 1}, balance=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
