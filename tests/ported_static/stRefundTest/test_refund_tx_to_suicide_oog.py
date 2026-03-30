"""
Test_refund_tx_to_suicide_oog.

Ported from:
state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json
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
    ["state_tests/stRefundTest/refund_TxToSuicideOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_tx_to_suicide_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_refund_tx_to_suicide_oog."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
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
        address=Address(0x2BC33A472F0FBA1E30BF2317D07910367908C7F6),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=21002,
        value=10,
    )

    post = {
        coinbase: Account(balance=0),
        sender: Account(balance=0x5F2AC9C, nonce=1),
        target: Account(storage={1: 1}, balance=0xDE0B6B3A7640000),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
