"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml

contract code:
    push2 0x60a7
    push1 0x00
    mstore
    push2 0x60a7
    push1 0x20
    mstore
    push2 0x60a7
    push1 0x40
    mstore
    gas
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push2 0x1000
    push3 0x010000
    call
    ... (33 more instructions)

callee code:
    push1 0x00
    push1 0xff
    return

callee_1 code:
    push1 0x00
    push1 0xff
    stop
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
    ["tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_gas_cost_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0x56724d001b4f2a2888a81971a64aad37cd43f881")
    contract = Address("0x155665fb22995bb5b9dc1d8d9d57a00ac64dc1e0")
    callee = Address("0x35cd99e56b0f9ac243172a86bef4d042dfdbc166")
    callee_1 = Address("0xeb0e68b88a12fc84ad4a1eeb07b289638c4d9f3c")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH2[0x60a7] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH2[0x60a7]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH2[0x60a7] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH2[0x1000]
        + Op.PUSH3[0x10000] + Op.CALL + Op.POP + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD
        + Op.SUB + Op.PUSH1[0x20] + Op.MSTORE + Op.GAS + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.PUSH3[0x10000] + Op.CALL + Op.POP
        + Op.GAS + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH1[0x40] + Op.MLOAD + Op.PUSH1[0x20] + Op.MLOAD + Op.SUB
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0x60a7},
    )
    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.RETURN,
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.STOP,
    )

    tx = Transaction(
        secret_key=Hash(
            "0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e"
        ),
        to=contract,
        data=bytes.fromhex("00"),
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
