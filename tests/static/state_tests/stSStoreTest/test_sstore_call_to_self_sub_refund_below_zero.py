"""
Test where accnt has slot 1 value of '2', is cleared, then calls itself and overwrites with '3', causing a refund-deduction in second call context

Ported from:
tests/static/state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json

contract code:
    caller
    address
    eq
    push1 0x15
    jumpi
    push1 0x00
    push1 0x01
    sstore
    push1 0x00
    dup1
    dup1
    dup1
    dup1
    address
    gas
    call
    stop
    jumpdest
    push1 0x03
    push1 0x01
    ... (2 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSStoreTest/SstoreCallToSelfSubRefundBelowZeroFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_call_to_self_sub_refund_below_zero(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test where accnt has slot 1 value of '2', is cleared, then calls itself and overwrites with '3', causing a refund-deduction in second call context."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x2c4b3807d1cb27f33e74c7cd5be5b0d6b176414e")
    contract = Address("0xb48023055b6c3d565a6f5488459d64efab79b6c7")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=68719476736,
    )

    pre[sender] = Account(balance=0xffffffffffffffff, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.CALLER + Op.ADDRESS + Op.EQ + Op.PUSH1[0x15] + Op.JUMPI + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.ADDRESS + Op.GAS + Op.CALL + Op.STOP + Op.JUMPDEST
        + Op.PUSH1[0x3] + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
        storage={0x1: 0x2},
    )

    tx = Transaction(
        secret_key=Hash(
            "0xaf50993ba9fd52f2a61fcd1dc6d59a44e7af39f4289201cc19ea7d30e8e27e83"
        ),
        to=contract,
        data=b"",
        gas_limit=2367154,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
