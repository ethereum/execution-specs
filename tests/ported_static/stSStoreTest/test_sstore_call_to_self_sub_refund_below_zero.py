"""
Test where accnt has slot 1 value of '2', is cleared, then calls itself...

Ported from:
state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json
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
    ["state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_sstore_call_to_self_sub_refund_below_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test where accnt has slot 1 value of '2', is cleared, then calls..."""
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFF)

    # Source: raw
    # 0x3330146015576000600155600080808080305af1005b600360015500
    target = pre.deploy_contract(
        code=Op.JUMPI(pc=0x15, condition=Op.EQ(Op.ADDRESS, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.CALL(
            gas=Op.GAS,
            address=Op.ADDRESS,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=0x3)
        + Op.STOP,
        storage={1: 2},
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2367154,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={1: 3}, balance=0, nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
