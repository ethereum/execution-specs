"""
Test_callcode_emptycontract.

Ported from:
state_tests/stCallCodes/callcodeEmptycontractFiller.json
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
    ["state_tests/stCallCodes/callcodeEmptycontractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_callcode_emptycontract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcode_emptycontract."""
    sender = pre.fund_eoa(amount=0x5F5E100)

    # Source: lll
    # { [[ 0 ]] (CALLCODE 50000 0x945304eb96065b2a98b57a48a06ae28d285a71b5 1000 0 64 0 64 )}  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0xC350,
                address=0x945304EB96065B2A98B57A48A06AE28D285A71B5,
                value=0x3E8,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=1000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1050440,
    )

    post = {target: Account(storage={0: 1})}

    state_test(pre=pre, post=post, tx=tx)
