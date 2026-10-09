"""
Test_suicide_caller_addres_too_big_left.

Ported from:
state_tests/stSystemOperationsTest/suicideCallerAddresTooBigLeftFiller.json
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
        "state_tests/stSystemOperationsTest/suicideCallerAddresTooBigLeftFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_suicide_caller_addres_too_big_left(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_caller_addres_too_big_left."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)
    too_big_address = int.from_bytes(b"\xaa" + bytes(sender), "big")

    # Source: lll
    # { [[0]] (CALLER) (SELFDESTRUCT 0xaaa94f5374fce5edbc8e2a8697c15331677e6ebf0b)}  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLER)
        + Op.SELFDESTRUCT(address=too_big_address)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(storage={0: sender}, balance=0, nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
