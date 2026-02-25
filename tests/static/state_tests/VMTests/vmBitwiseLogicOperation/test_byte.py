"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml

callee code:
    push1 0x00
    push2 0x0100
    mstore
    jumpdest
    push1 0x20
    push2 0x0100
    mload
    lt
    iszero
    push1 0x4a
    jumpi
    push31 0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f
    push2 0x0100
    mload
    byte
    push2 0x0100
    mload
    sstore
    push1 0x01
    push2 0x0100
    ... (8 more instructions)

callee_1 code:
    push8 0x8040201008040201
    push1 0x00
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_2 code:
    push8 0x8040201008040201
    push1 0x01
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_3 code:
    push8 0x8040201008040201
    push1 0x02
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_4 code:
    push8 0x8040201008040201
    push1 0x03
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_5 code:
    push8 0x8040201008040201
    push1 0x04
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_6 code:
    push8 0x8040201008040201
    push1 0x05
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_7 code:
    push8 0x8040201008040201
    push1 0x06
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_8 code:
    push8 0x8040201008040201
    push1 0x07
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_9 code:
    push8 0x8040201008040201
    push1 0x1f
    push1 0x1f
    sub
    byte
    push1 0x00
    sstore
    stop

callee_10 code:
    push8 0x8040201008040201
    push1 0x20
    push1 0x1f
    sdiv
    byte
    push1 0x00
    sstore
    stop

callee_11 code:
    push5 0x1234523456
    push1 0x1f
    byte
    dup1
    add
    push1 0x01
    sstore

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x04
    calldataload
    push3 0xffffff
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
    ["tests/static/state_tests/VMTests/vmBitwiseLogicOperation/byteFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "693c61390000000000000000000000000000000000000000000000000000000000001008",
        "693c61390000000000000000000000000000000000000000000000000000000000001009",
        "693c61390000000000000000000000000000000000000000000000000000000000001007",
        "693c61390000000000000000000000000000000000000000000000000000000000001006",
        "693c61390000000000000000000000000000000000000000000000000000000000001005",
        "693c61390000000000000000000000000000000000000000000000000000000000001004",
        "693c61390000000000000000000000000000000000000000000000000000000000001003",
        "693c61390000000000000000000000000000000000000000000000000000000000001002",
        "693c61390000000000000000000000000000000000000000000000000000000000001001",
        "693c61390000000000000000000000000000000000000000000000000000000000001000",
        "693c61390000000000000000000000000000000000000000000000000000000000000200",
        "693c6139000000000000000000000000000000000000000000000000000000000000100a",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11'],
)
@pytest.mark.pre_alloc_mutable
def test_byte(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    callee = Address("0x0000000000000000000000000000000000000200")
    callee_1 = Address("0x0000000000000000000000000000000000001000")
    callee_2 = Address("0x0000000000000000000000000000000000001001")
    callee_3 = Address("0x0000000000000000000000000000000000001002")
    callee_4 = Address("0x0000000000000000000000000000000000001003")
    callee_5 = Address("0x0000000000000000000000000000000000001004")
    callee_6 = Address("0x0000000000000000000000000000000000001005")
    callee_7 = Address("0x0000000000000000000000000000000000001006")
    callee_8 = Address("0x0000000000000000000000000000000000001007")
    callee_9 = Address("0x0000000000000000000000000000000000001008")
    callee_10 = Address("0x0000000000000000000000000000000000001009")
    callee_11 = Address("0x000000000000000000000000000000000000100a")

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
        code=(
        Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.MSTORE + Op.JUMPDEST + Op.PUSH1[0x20]
        + Op.PUSH2[0x100] + Op.MLOAD + Op.LT + Op.ISZERO + Op.PUSH1[0x4a] + Op.JUMPI
        + Op.PUSH31[0x102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f]
        + Op.PUSH2[0x100] + Op.MLOAD + Op.BYTE + Op.PUSH2[0x100] + Op.MLOAD
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH2[0x100] + Op.MLOAD + Op.ADD
        + Op.PUSH2[0x100] + Op.MSTORE + Op.PUSH1[0x6] + Op.JUMP + Op.JUMPDEST
        + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x0] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x1] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x2] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x3] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x4] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x5] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x6] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x7] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x1f] + Op.PUSH1[0x1f] + Op.SUB
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH8[0x8040201008040201] + Op.PUSH1[0x20] + Op.PUSH1[0x1f] + Op.SDIV
        + Op.BYTE + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_11] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH5[0x1234523456] + Op.PUSH1[0x1f] + Op.BYTE + Op.DUP1 + Op.ADD
        + Op.PUSH1[0x1] + Op.SSTORE
    ),
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce, nonce=0)
    pre[contract] = Account(
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.CALLDATALOAD + Op.PUSH3[0xffffff]
        + Op.CALL + Op.STOP
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
