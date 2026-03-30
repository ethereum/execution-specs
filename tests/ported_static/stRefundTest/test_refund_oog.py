"""
Test_refund_oog.

Ported from:
state_tests/stRefundTest/refund_OOGFiller.json
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
    ["state_tests/stRefundTest/refund_OOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_oog."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0x8518C6B13163F88376ADBDE956B3D6C1E4E027E25E20994C1AD0D78B8FD7FAC9
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
    # { [[ 1 ]] 0 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF4C9FC42FAEDA49049E3B8E2B97A17CC2FE95718),  # noqa: E501
    )
    pre[sender] = Account(balance=0x7A120)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=26005,
        value=10,
    )

    post = {
        target: Account(storage={1: 1}, balance=0xDE0B6B3A7640000),
        coinbase: Account(balance=0),
        sender: Account(balance=0x3A94E, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
