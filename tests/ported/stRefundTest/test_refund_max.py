"""
Ori Pomerantz   qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stRefundTest/refundMaxFiller.yml

contract code:
    push1 0x00
    dup1
    push1 0x00
    sstore
    dup1
    push1 0x01
    sstore
    dup1
    push1 0x02
    sstore
    dup1
    push1 0x03
    sstore
    dup1
    push1 0x04
    sstore
    dup1
    push1 0x05
    sstore
    dup1
    ... (5 more instructions)
"""

import pytest
from execution_testing import (
    AccessList,
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
    ["tests/static/state_tests/stRefundTest/refundMaxFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_refund_max(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xe9d050af4e864e83c38a83b4b69407e6ff3c70c5")
    contract = Address("0x7e9d1ff50f8eb9591a0434abfe3230054a934124")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=1000,
        gas_limit=16777216,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.PUSH1[0x0] + Op.DUP1 + Op.PUSH1[0x0] + Op.SSTORE + Op.DUP1
        + Op.PUSH1[0x1] + Op.SSTORE + Op.DUP1 + Op.PUSH1[0x2] + Op.SSTORE + Op.DUP1
        + Op.PUSH1[0x3] + Op.SSTORE + Op.DUP1 + Op.PUSH1[0x4] + Op.SSTORE + Op.DUP1
        + Op.PUSH1[0x5] + Op.SSTORE + Op.DUP1 + Op.PUSH1[0x6] + Op.SSTORE
        + Op.PUSH1[0x7] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7, 0x1: 0x60a7, 0x2: 0x60a7, 0x3: 0x60a7, 0x4: 0x60a7, 0x5: 0x60a7, 0x6: 0x60a7, 0x7: 0x60a7},
    )
    pre[sender] = Account(balance=0xe8d848c3a0, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xb5555c6f8171a6eb3c0a84ed8f01af5ce65a85a096a824a60ee5e2c2c2e076d1"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=2601000,
        gas_price=1000,
        nonce=1,
        value=0,
        access_list=[],
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
