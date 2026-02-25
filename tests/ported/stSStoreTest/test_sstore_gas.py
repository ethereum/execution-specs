"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stSStoreTest/sstoreGasFiller.yml

contract code:
    push1 0x01
    push1 0x08
    dup2
    dup1
    dup1
    dup1
    dup1
    dup1
    dup1
    dup1
    push2 0x1000
    dup10
    gas
    push2 0xbeef
    push1 0x00
    sstore
    gas
    swap1
    sub
    sub
    ... (113 more instructions)
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
    ["tests/static/state_tests/stSStoreTest/sstoreGasFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_sstore_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x485fd0fd5c1d0409d2b772a66e98a6ac867b9d8b")
    contract = Address("0x84e1dc6705b8b9b7ffaca256c9266792bdd0943b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=1)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=1,
        code=(
        Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.DUP2 + Op.DUP1 + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.DUP1 + Op.PUSH2[0x1000] + Op.DUP10 + Op.GAS
        + Op.PUSH2[0xbeef] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB
        + Op.SUB + Op.DUP2 + Op.SSTORE + Op.ADD + Op.DUP9 + Op.GAS
        + Op.PUSH4[0xdeadbeef] + Op.PUSH1[0x0] + Op.SSTORE + Op.GAS + Op.SWAP1
        + Op.SUB + Op.SUB + Op.DUP2 + Op.SSTORE + Op.ADD + Op.DUP8 + Op.GAS
        + Op.PUSH1[0x0] + Op.DUP1 + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB
        + Op.DUP2 + Op.SSTORE + Op.ADD + Op.DUP7 + Op.GAS + Op.PUSH1[0x0] + Op.DUP1
        + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB + Op.DUP2 + Op.SSTORE
        + Op.ADD + Op.DUP6 + Op.GAS + Op.PUSH2[0x1234] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB + Op.DUP2 + Op.SSTORE + Op.ADD + Op.DUP5
        + Op.GAS + Op.PUSH1[0x0] + Op.DUP5 + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB
        + Op.SUB + Op.DUP2 + Op.SSTORE + Op.ADD + Op.DUP4 + Op.GAS + Op.PUSH2[0x60a7]
        + Op.PUSH1[0x2] + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB + Op.DUP2
        + Op.SSTORE + Op.ADD + Op.DUP3 + Op.GAS + Op.PUSH1[0x0] + Op.PUSH1[0x3]
        + Op.SSTORE + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB + Op.DUP2 + Op.SSTORE
        + Op.ADD + Op.SWAP1 + Op.GAS + Op.PUSH2[0x60a7] + Op.PUSH1[0x3] + Op.SSTORE
        + Op.GAS + Op.SWAP1 + Op.SUB + Op.SUB + Op.DUP2 + Op.SSTORE + Op.POP + Op.POP
        + Op.PUSH1[0x0] + Op.DUP1 + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x3] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7, 0x1: 0x60a7},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x48dc5a9f099caaaa557742ca3a990a94be45b9969126a1bc74e5e8be5a2b5b47"
        ),
        to=contract,
        data=b"",
        gas_limit=16777216,
        gas_price=10,
        nonce=1,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
