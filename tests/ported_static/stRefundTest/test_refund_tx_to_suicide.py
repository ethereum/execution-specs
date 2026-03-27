"""
Test_refund_tx_to_suicide.

Ported from:
state_tests/stRefundTest/refund_TxToSuicideFiller.json
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
    ["state_tests/stRefundTest/refund_TxToSuicideFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_tx_to_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_tx_to_suicide."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0x5F5E100)
    # Source: lll
    # { (SELFDESTRUCT 0x095e7baea6a6c7c4c2dfeb977efac326af552d87) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x95E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
        + Op.STOP,
        storage={1: 1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x2bc33a472f0fba1e30bf2317d07910367908c7f6"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=61003,
        value=10,
        gas_price=10,
    )

    post = {
        Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"): Account(
            storage={}, balance=0xDE0B6B3A764000A
        ),
        coinbase: Account(balance=0),
        sender: Account(balance=0x5EDB318, nonce=1),
        target: Account(storage={1: 1}, balance=0, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
