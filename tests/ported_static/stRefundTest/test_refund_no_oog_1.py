"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRefundTest/refund_NoOOG_1Filler.json
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
    ["tests/static/state_tests/stRefundTest/refund_NoOOG_1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_no_oog_1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x791307ECE6DFD40DF62DC66EFBC482096DD34650382AEB5D46DBEEDED66508F7
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xA03F70)
    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: LLL
    # { [[ 1 ]] 0 }
    contract = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=26006,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
