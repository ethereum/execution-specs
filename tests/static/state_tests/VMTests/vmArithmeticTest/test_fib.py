"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/fibFiller.yml

contract code:
    push1 0x02
    push1 0x02
    sub
    sload
    push1 0x01
    push1 0x02
    sub
    sload
    add
    push1 0x02
    sstore
    push1 0x02
    push1 0x03
    sub
    sload
    push1 0x01
    push1 0x03
    sub
    sload
    add
    ... (80 more instructions)
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
    ["tests/static/state_tests/VMTests/vmArithmeticTest/fibFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_fib(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0xf8d9ff3e0cf16acf51098c85f2cb8f082ef588c2")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH1[0x2] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x3] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x3] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x4] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x4] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x4] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x5] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x5] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x5] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x6] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x6] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x6] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x7] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x7] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x7] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x8] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x8] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x8] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0x9] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0x9] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0x9] + Op.SSTORE
        + Op.PUSH1[0x2] + Op.PUSH1[0xa] + Op.SUB + Op.SLOAD + Op.PUSH1[0x1]
        + Op.PUSH1[0xa] + Op.SUB + Op.SLOAD + Op.ADD + Op.PUSH1[0xa] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0x0, 0x1: 0x1},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=bytes.fromhex("01"),
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
