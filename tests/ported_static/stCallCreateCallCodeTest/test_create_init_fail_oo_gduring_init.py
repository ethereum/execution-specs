"""
Create fails because init code has OOG.

Ported from:
state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInitFiller.json
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
    [
        "state_tests/stCallCreateCallCodeTest/createInitFail_OOGduringInitFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_init_fail_oo_gduring_init(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Create fails because init code has OOG."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {(MSTORE8 0 0x5a ) (SELFDESTRUCT (CREATE 1 0 1)) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE8(offset=0x0, value=0x5A)
        + Op.SELFDESTRUCT(address=Op.CREATE(value=0x1, offset=0x0, size=0x1))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=53021,
        value=0x186A0,
    )

    post = {
        Address(
            0x0000000000000000000000000000000000000000
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
