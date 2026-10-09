"""
Test_balance_input_address_too_big.

Ported from:
state_tests/stSystemOperationsTest/balanceInputAddressTooBigFiller.json
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
        "state_tests/stSystemOperationsTest/balanceInputAddressTooBigFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_balance_input_address_too_big(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_balance_input_address_too_big."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)
    too_big_address = int.from_bytes(bytes(sender) + b"\xaa", "big")

    # Source: lll
    # { [[ 0 ]] (BALANCE <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b>aa ) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.BALANCE(address=too_big_address),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=300000,
        value=0x186A0,
    )

    post = {target: Account(storage={}, nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
