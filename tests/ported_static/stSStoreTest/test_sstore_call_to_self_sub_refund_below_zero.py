"""
Test where accnt has slot 1 value of '2', is cleared, then calls itself and overwrites with '3', causing a refund-deduction in second call context

Ported from:
state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json
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
    ["state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_call_to_self_sub_refund_below_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test where accnt has slot 1 value of '2', is cleared, then calls it..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xaf50993ba9fd52f2a61fcd1dc6d59a44e7af39f4289201cc19ea7d30e8e27e83
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=68719476736,
    )

    # Source: raw
    # 0x3330146015576000600155600080808080305af1005b600360015500
    target = pre.deploy_contract(
        code=Op.JUMPI(pc=0x15, condition=Op.EQ(Op.ADDRESS, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.CALL(gas=Op.GAS, address=Op.ADDRESS, value=Op.DUP1, args_offset=Op.DUP1, args_size=Op.DUP1, ret_offset=Op.DUP1, ret_size=0x0)
        + Op.STOP + Op.JUMPDEST + Op.SSTORE(key=0x1, value=0x3) + Op.STOP,
        storage={1: 2},
        nonce=0,
        address=Address("0xb48023055b6c3d565a6f5488459d64efab79b6c7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xffffffffffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=2367154,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={1: 3}, balance=0, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
