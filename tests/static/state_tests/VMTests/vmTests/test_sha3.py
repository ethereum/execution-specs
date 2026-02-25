"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmTests/sha3Filler.yml

callee code:
    push1 0x00
    push1 0x00
    sha3
    push1 0x00
    sstore
    stop

callee_1 code:
    push1 0x05
    push1 0x04
    sha3
    push1 0x00
    sstore
    stop

callee_2 code:
    push1 0x0a
    push1 0x0a
    sha3
    push1 0x00
    sstore
    stop

callee_3 code:
    push3 0x0fffff
    push2 0x03e8
    sha3
    push1 0x00
    sstore
    stop

callee_4 code:
    push1 0x64
    push5 0x0fffffffff
    sha3
    push1 0x00
    sstore
    stop

callee_5 code:
    push5 0x0fffffffff
    push2 0x2710
    sha3
    push1 0x00
    sstore
    stop

callee_6 code:
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    sha3
    push1 0x00
    sstore
    stop

callee_7 code:
    push1 0x02
    push32 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    sha3
    push1 0x00
    sstore
    stop

callee_8 code:
    push1 0x02
    push4 0x01000000
    sha3
    push1 0x00
    sstore
    stop

callee_9 code:
    push1 0x01
    push2 0x03c0
    sha3
    push1 0x00
    sstore
    stop

callee_10 code:
    push1 0x01
    push2 0x03e0
    sha3
    push1 0x00
    sstore
    stop

callee_11 code:
    push1 0x01
    push2 0x0400
    sha3
    push1 0x00
    sstore
    stop

callee_12 code:
    push1 0x01
    push2 0x07c0
    sha3
    push1 0x00
    sstore
    stop

callee_13 code:
    push1 0x01
    push2 0x07e0
    sha3
    push1 0x00
    sstore
    stop

callee_14 code:
    push1 0x01
    push2 0x0800
    sha3
    push1 0x00
    sstore
    stop

callee_15 code:
    push1 0x00
    push2 0x0400
    sha3
    push1 0x00
    sstore
    stop

callee_16 code:
    push1 0x20
    push2 0x07e0
    sha3
    push1 0x00
    sstore
    stop

contract code:
    push1 0x40
    push1 0x20
    push1 0x10
    push1 0x0f
    push1 0x00
    push1 0x04
    calldataload
    push2 0x1000
    add
    push1 0x01
    push1 0x00
    sub
    call
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
    ["tests/static/state_tests/VMTests/vmTests/sha3Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000000008",
        "693c61390000000000000000000000000000000000000000000000000000000000000003",
        "693c6139000000000000000000000000000000000000000000000000000000000000000f",
        "693c6139000000000000000000000000000000000000000000000000000000000000000b",
        "693c6139000000000000000000000000000000000000000000000000000000000000000c",
        "693c6139000000000000000000000000000000000000000000000000000000000000000d",
        "693c61390000000000000000000000000000000000000000000000000000000000000010",
        "693c6139000000000000000000000000000000000000000000000000000000000000000e",
        "693c61390000000000000000000000000000000000000000000000000000000000000009",
        "693c6139000000000000000000000000000000000000000000000000000000000000000a",
        "693c61390000000000000000000000000000000000000000000000000000000000000001",
        "693c61390000000000000000000000000000000000000000000000000000000000000004",
        "693c61390000000000000000000000000000000000000000000000000000000000000005",
        "693c61390000000000000000000000000000000000000000000000000000000000000007",
        "693c61390000000000000000000000000000000000000000000000000000000000000006",
        "693c61390000000000000000000000000000000000000000000000000000000000000000",
        "693c61390000000000000000000000000000000000000000000000000000000000000002",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16'],
)
@pytest.mark.pre_alloc_mutable
def test_sha3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x0000000000000000000000000000000000001000")
    callee_1 = Address("0x0000000000000000000000000000000000001001")
    callee_2 = Address("0x0000000000000000000000000000000000001002")
    callee_3 = Address("0x0000000000000000000000000000000000001003")
    callee_4 = Address("0x0000000000000000000000000000000000001004")
    callee_5 = Address("0x0000000000000000000000000000000000001005")
    callee_6 = Address("0x0000000000000000000000000000000000001006")
    callee_7 = Address("0x0000000000000000000000000000000000001007")
    callee_8 = Address("0x0000000000000000000000000000000000001008")
    callee_9 = Address("0x0000000000000000000000000000000000001009")
    callee_10 = Address("0x000000000000000000000000000000000000100a")
    callee_11 = Address("0x000000000000000000000000000000000000100b")
    callee_12 = Address("0x000000000000000000000000000000000000100c")
    callee_13 = Address("0x000000000000000000000000000000000000100d")
    callee_14 = Address("0x000000000000000000000000000000000000100e")
    callee_15 = Address("0x000000000000000000000000000000000000100f")
    callee_16 = Address("0x0000000000000000000000000000000000001010")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x5] + Op.PUSH1[0x4] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0xa] + Op.PUSH1[0xa] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH3[0xfffff] + Op.PUSH2[0x3e8] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x64] + Op.PUSH5[0xfffffffff] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH5[0xfffffffff] + Op.PUSH2[0x2710] + Op.SHA3 + Op.PUSH1[0x0]
        + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x2]
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x2] + Op.PUSH4[0x1000000] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE
        + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x3c0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x3e0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x400] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_12] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x7c0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_13] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x7e0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_14] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x1] + Op.PUSH2[0x800] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_15] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x0] + Op.PUSH2[0x400] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[callee_16] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=Op.PUSH1[0x20] + Op.PUSH2[0x7e0] + Op.SHA3 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP,
    )
    pre[sender] = Account(balance=0x100000000000, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x20] + Op.PUSH1[0x10] + Op.PUSH1[0xf]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH2[0x1000] + Op.ADD
        + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.SUB + Op.CALL + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
