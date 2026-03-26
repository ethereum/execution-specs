"""
test_refund_get_ether_back

Ported from:
state_tests/stRefundTest/refund_getEtherBackFiller.json
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
    ["state_tests/stRefundTest/refund_getEtherBackFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_get_ether_back(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_refund_get_ether_back"""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0x29268b0c3308094249e9a06c02739f688d492d6325ca24b36ef949e5fc20af27
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=228500,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # { [[ 1 ]] 0 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3cf773d0)


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
        target: Account(storage={}, balance=0xde0b6b3a764000a),
        coinbase: Account(balance=0),
        sender: Account(balance=0x3cf4376a, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
