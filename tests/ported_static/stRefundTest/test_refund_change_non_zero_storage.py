"""
Test_refund_change_non_zero_storage.

Ported from:
state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_change_non_zero_storage."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x4D9FC6FDF95098986741EE78843AC52BEED77C8C801DC87BD3F04CD6BBF1A3EB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 23 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x17) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x904261B07D3A5F213BBD6FB9F3BB66F4FB65C7EB),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3C336080)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=228500,
        value=10,
    )

    post = {
        target: Account(storage={1: 23}, balance=0xDE0B6B3A764000A),
        coinbase: Account(balance=0),
        sender: Account(balance=0x3C2F689A, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
