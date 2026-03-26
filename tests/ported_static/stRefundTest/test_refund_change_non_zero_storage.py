"""
test_refund_change_non_zero_storage

Ported from:
state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json
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
    ["state_tests/stRefundTest/refund_changeNonZeroStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_change_non_zero_storage(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_refund_change_non_zero_storage"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x4d9fc6fdf95098986741ee78843ac52beed77c8c801dc87bd3f04cd6bbf1a3eb
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 23 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x17) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x904261b07d3a5f213bbd6fb9f3bb66f4fb65c7eb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3c336080)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=228500,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={1: 23}, balance=0xde0b6b3a764000a),
        coinbase: Account(balance=0),
        sender: Account(balance=0x3c2f689a, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
