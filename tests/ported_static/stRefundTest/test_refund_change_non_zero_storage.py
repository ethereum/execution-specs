"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
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

    pre[sender] = Account(balance=0x3C336080)
    # Source: LLL
    # { [[ 1 ]] 23 }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x17) + Op.STOP,
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x904261b07d3a5f213bbd6fb9f3bb66f4fb65c7eb"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=228500,
        value=10,
    )

    post = {
        contract: Account(storage={1: 23}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
