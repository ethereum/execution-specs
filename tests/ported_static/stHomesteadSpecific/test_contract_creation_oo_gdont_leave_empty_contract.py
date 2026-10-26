"""
Test_contract_creation_oo_gdont_leave_empty_contract.

Ported from:
state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractFiller.json
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
        "state_tests/stHomesteadSpecific/contractCreationOOGdontLeaveEmptyContractFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_contract_creation_oo_gdont_leave_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_contract_creation_oo_gdont_leave_empty_contract."""
    sender = pre.fund_eoa(amount=0xF4240)

    # Source: lll
    # { (SSTORE 1 0x10) (MSTORE 0 0x6001600155601080600c6000396000f3006000355415600957005b6020356000 ) (CREATE 0 0 32)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x10)
        + Op.MSTORE(
            offset=0x0,
            value=0x6001600155601080600C6000396000F3006000355415600957005B6020356000,  # noqa: E501
        )
        + Op.CREATE(value=0x0, offset=0x0, size=0x20)
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=93056,
    )

    post = {
        compute_create_address(
            address=contract_0, nonce=1
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
